"""P12.6-3 identity/association tests; no native emitter or serializer."""
from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from air.model import VerifiedAIRProgram
from air.verify import AIRVerifier
from language.compiler import SourceMap, SourceMapEntry, compile_source_with_map
from language.source import SourcePosition, SourceSpan, SourceText
from apexforge.native_backend.lowering_input import build_verified_air_lowering_input
from apexforge.native_backend.native_execution_contract import admit_native_profile, NativeExecutionError
from tooling.debug_metadata import (SourceIdentity, StateLocator, AssignmentLocator, AIRMetadataIdentity,
    OperationReference, EvidenceReference, MetadataSidecar, MetadataAssociation)
from p12_5_native_profile_contract_test import fixture, plan_for, with_path

SOURCE = """directive Main {
    state count = 0
    cause start {
        path primary @ 10 {
            set count = 1
            set count = 1
        }
    }
}
"""


def references(verified):
    # Test producer supplies structural references; metadata never infers a bridge.
    program = verified.program
    fingerprint = build_verified_air_lowering_input(verified).transport_fingerprint
    identities = tuple(AIRMetadataIdentity(fingerprint, StateLocator(i, state.id))
                       for i, state in enumerate(program.states))
    d = program.directives[0]
    decision = program.causal_decisions[0]
    path = decision.paths[0]
    identities += tuple(AIRMetadataIdentity(fingerprint, AssignmentLocator(
        0, d.id, 0, decision.id, 0, path.id, i)) for i in range(len(path.assignments)))
    return identities


def foundation(program=None):
    program = fixture() if program is None else program
    verified = AIRVerifier().verify(program).require_verified()
    required = references(verified)
    # Admitted hand-authored AIR has no authentic source correspondence.
    sidecar = MetadataSidecar((), required[0].air_fingerprint, SourceMap(),
                             tuple(OperationReference(i, x) for i, x in enumerate(required)))
    return verified, sidecar, required


class MetadataTests(unittest.TestCase):
    def test_source_identity_and_portability(self):
        raw = "α\r\nβ\n".encode("utf-8")
        first = SourceIdentity.from_bytes("src/main.apex", raw)
        self.assertEqual(first.fingerprint(), SourceIdentity.from_bytes("src/main.apex", raw).fingerprint())
        self.assertNotEqual(first.fingerprint(), SourceIdentity.from_bytes("src/main.apex", raw + b" ").fingerprint())
        self.assertNotEqual(first.fingerprint(), SourceIdentity.from_bytes("other/main.apex", raw).fingerprint())
        for name in ("C:/host/main.apex", "C:main.apex", "/tmp/main.apex", "//host/share/main.apex",
                     "../main.apex", "src/./main.apex", "src//main.apex", "src\\main.apex", " main.apex", "src/\nmain"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                SourceIdentity.from_bytes(name, raw)
        with self.assertRaises(ValueError):
            first.validate_content(raw + b"changed")
        with self.assertRaises(FrozenInstanceError):
            first.logical_name = "changed"
        # A root/path/time/PID input is absent from the identity API, rather than filtered after hashing.
        with self.assertRaises(TypeError):
            SourceIdentity("main.apex", first.content_fingerprint, root="C:/host")

    def test_air_equivalence_and_occurrences(self):
        v, s, required = foundation()
        copy_v, copy_s, copy_required = foundation(replace(v.program))
        self.assertEqual(required, copy_required)
        self.assertEqual(tuple(x.fingerprint() for x in required), tuple(x.fingerprint() for x in copy_required))
        self.assertEqual(s.fingerprint(), copy_s.fingerprint())
        self.assertEqual(tuple(x.operation_id for x in s.operations), tuple(x.operation_id for x in copy_s.operations))
        s.validate(copy_v, (), required)
        repeated = with_path(v.program, assignments=(v.program.causal_decisions[0].paths[0].assignments[0],) * 2)
        rv, rs, rr = foundation(repeated)
        self.assertNotEqual(rs.operations[-1].operation_id, rs.operations[-2].operation_id)
        rs.validate(rv, (), rr)
        with self.assertRaises(ValueError):
            rs.validate(rv, (), rr[:-1])
        with self.assertRaises(ValueError):
            rs.validate(rv, (), tuple(reversed(rr)))
        reordered = with_path(v.program, assignments=tuple(reversed(v.program.causal_decisions[0].paths[0].assignments)))
        changed_v, _, _ = foundation(reordered)
        with self.assertRaises(ValueError):
            s.validate(changed_v, (), required)

    def test_operation_order_duplicate_and_missing(self):
        v, s, required = foundation()
        with self.assertRaises(ValueError):
            replace(s, operations=tuple(reversed(s.operations)))
        with self.assertRaises(ValueError):
            replace(s, operations=(s.operations[0], s.operations[0]))
        duplicate = OperationReference(1, s.operations[0].identity)
        with self.assertRaises(ValueError):
            replace(s, operations=(s.operations[0], duplicate))
        partial = replace(s, operations=s.operations[:-1])
        with self.assertRaises(ValueError):
            partial.validate(v, (), required)
        missing = EvidenceReference("af-meta-op:" + "0" * 64, 0, 0)
        with self.assertRaises(ValueError):
            replace(s, evidence=(missing,))
        with self.assertRaises(ValueError):
            OperationReference(-1, required[0])

    def test_bad_locator_and_inference_reject(self):
        v, s, required = foundation()
        locator = required[-1].locator
        for bad in (replace(locator, assignment_index=99), replace(locator, path_index=99),
                    replace(locator, decision_occurrence=99), replace(locator, directive_index=99),
                    replace(locator, path_id="path:missing"), replace(locator, decision_id="cause:missing"),
                    replace(locator, directive_id="Main")):
            with self.subTest(locator=bad), self.assertRaises(ValueError):
                AIRMetadataIdentity(s.air_fingerprint, bad).validate(v)
        for index in (-1, True, 1.5, "0"):
            with self.assertRaises(ValueError):
                replace(locator, assignment_index=index)
        with self.assertRaises(ValueError):
            AIRMetadataIdentity(s.air_fingerprint, "resolve Main by name")
        # Even a forged verified wrapper with an ambiguous canonical reference fails closed.
        p = v.program
        for ambiguous in (replace(p, causal_decisions=p.causal_decisions * 2),
                          replace(p, directives=p.directives * 2),
                          replace(p, states=p.states + (p.states[0],)),
                          replace(p, causal_decisions=(replace(p.causal_decisions[0],
                              paths=p.causal_decisions[0].paths * 2),))):
            forged = VerifiedAIRProgram(ambiguous)
            fp = build_verified_air_lowering_input(forged).transport_fingerprint
            target = required[0].locator if len(ambiguous.states) != len(p.states) else locator
            with self.assertRaises(ValueError):
                AIRMetadataIdentity(fp, target).validate(forged)

    def test_source_map_span_and_stale_source(self):
        raw = "α\r\nβ\n".encode("utf-8")
        text = SourceText("src/main.apex", raw.decode("utf-8"))
        source = SourceIdentity.from_bytes(text.name, raw)
        v, bare, required = foundation()
        entry = SourceMapEntry("compiler:evidence", text.span(0, len(text.text)), "observed")
        # This evidence is source-only; no source→operation mapping is inferred.
        sidecar = replace(bare, sources=(source,), source_map=SourceMap((entry, entry)))
        sidecar.validate(v, (raw,), required)
        self.assertEqual(len(sidecar.source_map.entries), 2)
        self.assertEqual(sidecar.fingerprint(), replace(sidecar).fingerprint())
        with self.assertRaises(ValueError):
            sidecar.validate(v, (raw + b"x",), required)
        malformed = SourceSpan(text.name, SourcePosition(9, 1, 0), text.position(len(text.text)))
        with self.assertRaises(ValueError):
            replace(sidecar, source_map=SourceMap((replace(entry, span=malformed),))).validate(v, (raw,), required)
        with self.assertRaises(ValueError):
            replace(sidecar, sources=(source, replace(source, logical_name="SRC/main.apex")))
        for field in ("air_id", "kind", "reference"):
            with self.assertRaises(ValueError):
                replace(sidecar, source_map=SourceMap((replace(entry, **{field: "C:/host/log"}),)))
        eof = SourceMapEntry("eof", text.span(len(text.text), len(text.text)))
        replace(sidecar, source_map=SourceMap((eof,))).validate(v, (raw,), required)
        with self.assertRaises(ValueError):
            replace(sidecar, source_map=SourceMap((replace(entry, span=SourceText("C:/host/a", "").span(0, 0)),)))
        with self.assertRaises(ValueError):
            replace(sidecar, sources=(source, source))
        with self.assertRaises(ValueError):
            replace(sidecar, evidence=(EvidenceReference(sidecar.operations[0].operation_id, 0, 99),))
        ref = EvidenceReference(sidecar.operations[0].operation_id, 0, 0)
        explicit = replace(sidecar, evidence=(ref,))
        explicit.validate(v, (raw,), required)
        with self.assertRaises(ValueError):
            replace(sidecar, evidence=(ref, ref))
        with self.assertRaises(FrozenInstanceError):
            explicit.operations = ()

    def test_plan_association_and_mismatch(self):
        v, s, required = foundation()
        plan = plan_for(v.program)
        a = MetadataAssociation.for_plan(s, v, plan, (), required)
        a.validate(s, v, plan, (), required)
        self.assertEqual(a.fingerprint(), MetadataAssociation.for_plan(s, v, plan, (), required).fingerprint())
        for bad in (replace(a, sidecar_fingerprint="0" * 64), replace(a, air_fingerprint="0" * 64),
                    replace(a, routing_fingerprint="0" * 64), replace(a, entry_directive="directive:other"),
                    replace(a, owner_fingerprints=())):
            with self.assertRaises(ValueError):
                bad.validate(s, v, plan, (), required)
        with self.assertRaises(ValueError):
            a.validate(s, v, replace(plan, entry_directive="main"), (), required)
        changed = with_path(v.program, assignments=(replace(v.program.causal_decisions[0].paths[0].assignments[0], value=99),))
        changed_v, _, _ = foundation(changed)
        with self.assertRaises(ValueError):
            a.validate(s, changed_v, plan_for(changed), (), required)
        owner_plan = replace(plan, directive_owners={plan.entry_directive.casefold(): changed})
        with self.assertRaises(ValueError):
            a.validate(s, v, owner_plan, (), required)
        with self.assertRaises(ValueError):
            MetadataAssociation.for_plan(s, v, replace(plan, directive_owners={
                plan.entry_directive.casefold(): replace(v.program, directives=())}), (), required)
        altered_sidecar = replace(s, sources=(SourceIdentity.from_bytes("main.apex", b"comment"),))
        with self.assertRaises(ValueError):
            a.validate(altered_sidecar, v, plan, (b"comment",), required)

    def test_real_compiler_actions_unchanged(self):
        artifact = compile_source_with_map(SOURCE, source_name="src/main.apex")
        verified = AIRVerifier().verify(artifact.program).require_verified()
        before = build_verified_air_lowering_input(verified).transport_json
        actions = artifact.program.causal_decisions[0].paths[0].actions
        self.assertTrue(actions)
        required = references(verified)
        sidecar = MetadataSidecar((SourceIdentity.from_bytes("src/main.apex", SOURCE.encode()),),
            required[0].air_fingerprint, artifact.source_map,
            tuple(OperationReference(i, x) for i, x in enumerate(required)))
        plan = plan_for(artifact.program)
        a = MetadataAssociation.for_plan(sidecar, verified, plan, (SOURCE.encode(),), required)
        a.validate(sidecar, verified, plan, (SOURCE.encode(),), required)
        self.assertIs(artifact.program.causal_decisions[0].paths[0].actions, actions)
        self.assertEqual(before, build_verified_air_lowering_input(verified).transport_json)
        with self.assertRaises(NativeExecutionError):
            admit_native_profile(verified, plan)
        self.assertEqual(tuple(f.name for f in fields(VerifiedAIRProgram)), ("program",))
        self.assertEqual(tuple(f.name for f in fields(type(plan))), ("program", "entry_directive", "directive_owners"))

    def test_no_second_semantics_and_no_execution_dependency(self):
        source = (ROOT / "apexforge/tooling/debug_metadata.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        allowed = {"__future__", "dataclasses", "hashlib", "json", "re", "typing", "air.model",
            "language.compiler", "language.source", "apexforge.native_backend.lowering_input",
            "apexforge.native_backend.execution_plan_binding"}
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertLessEqual(imports, allowed)
        self.assertEqual({n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)}, {"json", "re"})
        calls = {n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, (ast.Attribute, ast.Name))}
        self.assertFalse(calls & {"id", "eval", "exec", "execute", "verify", "compile_source_with_map",
            "resolve", "resolve_type", "infer_type", "select_path", "admit_native_profile", "write_text", "open"})
        v, s, required = foundation()
        with patch("runtime.engine.RuntimeEngine.execute", side_effect=AssertionError("metadata executed semantics")), \
             patch("air.verify.AIRVerifier.verify", side_effect=AssertionError("metadata verified semantics")), \
             patch("language.compiler.compile_source_with_map", side_effect=AssertionError("metadata recompiled")), \
             patch("subprocess.Popen", side_effect=AssertionError("metadata launched process")):
            s.validate(v, (), required)
            MetadataAssociation.for_plan(s, v, plan_for(v.program), (), required)


if __name__ == "__main__":
    unittest.main(verbosity=2)
