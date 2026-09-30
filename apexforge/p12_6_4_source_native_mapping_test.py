"""P12.6-4 producer correspondence, provenance and live native neutrality."""
from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from air.verify import AIRVerifier
from air.model import VerifiedAIRProgram
from language.compiler import (SourceMap, compile_source_with_map, compile_source_with_operation_evidence,
                               _compile_directive_with_map)
from language.parser import parse_source_unit
from language.source import SourceText, SourceSpan, SourcePosition
from tooling.debug_metadata import SourceIdentity, OperationReference, AIRMetadataIdentity, MetadataAssociation
from tooling.source_air_mapping import source_air_mapping, SourceCorrespondence, StructuralLineage
from apexforge.native_backend import native_execution as native
from apexforge.native_backend.source_mapping import (emit_native_source_mapping, GeneratedRegion,
                                                    build_native_with_mapping)
from apexforge.native_backend.native_execution_contract import NativeExecutionError
from apexforge.native_backend.lowering_input import build_verified_air_lowering_input
from workflow.air_runner import run_air_program
from p12_5_native_profile_contract_test import fixture, plan_for, with_path
from p12_6_3_metadata_identity_association_test import SOURCE


def compiler_fixture(source=SOURCE):
    compiled, ledger = compile_source_with_operation_evidence(source, source_name="src/main.apex")
    verified = AIRVerifier().verify(compiled.program).require_verified()
    governed = SourceIdentity.from_bytes("src/main.apex", source.encode("utf-8"))
    mapping = source_air_mapping(compiled, ledger, verified, governed, source.encode("utf-8"))
    return compiled, ledger, verified, governed, mapping


def native_fixture(program=None):
    program = fixture() if program is None else program
    verified = AIRVerifier().verify(program).require_verified()
    plan = plan_for(program)
    content, mapping = emit_native_source_mapping(verified, plan)
    return verified, plan, content, mapping


def frozen_emitter():
    source = subprocess.check_output(["git", "show", "afp-p12.5-execution-freeze:apexforge/native_backend/native_execution.py"],
                                     cwd=ROOT, text=True, encoding="utf-8")
    tree = ast.parse(source)
    tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("_source", "_constant")]
    namespace = {}
    exec(compile(tree, "frozen-emitter-test-oracle", "exec"), namespace)
    return namespace["_source"]


class MappingTests(unittest.TestCase):
    def test_real_producer_and_source_air_determinism(self):
        a, ledger, v, governed, mapping = compiler_fixture()
        b, ledger2, v2, governed2, mapping2 = compiler_fixture()
        ordinary = compile_source_with_map(SOURCE, source_name="src/main.apex")
        self.assertEqual(ordinary, a)
        self.assertEqual(a.source_map, b.source_map)
        self.assertEqual(ledger, ledger2)
        self.assertEqual(mapping.canonical_form(), mapping2.canonical_form())
        self.assertEqual(mapping.fingerprint(), mapping2.fingerprint())
        mapping.validate(a, ledger, v, governed, SOURCE.encode())
        self.assertEqual(len(mapping.correspondence), 3)
        self.assertTrue(all(r.category == "SOURCE_BACKED" for r in mapping.correspondence))
        ids = tuple(op.operation_id for op in mapping.sidecar.operations)
        self.assertEqual(len(set(ids)), 3)
        for record in mapping.correspondence:
            entry = a.source_map.entries[record.source_map_index]
            snippet = SOURCE[entry.span.start.offset:entry.span.end.offset]
            self.assertTrue("state count" in snippet or "set count" in snippet)
        for record in mapping.lineage:
            if record.category in ("COMPILER_SYNTHETIC", "GENERATED_CONTAINER", "METADATA_ONLY"):
                self.assertEqual(record.source_map_index, -1)
        self.assertTrue(any(r.category == "COMPILER_SYNTHETIC" and r.originating_entry_index >= 0 for r in mapping.lineage))
        with self.assertRaises(ValueError):
            StructuralLineage("synthetic", "COMPILER_SYNTHETIC", 0)

    def test_missing_and_ambiguous_source_correspondence(self):
        a, ledger, v, source, mapping = compiler_fixture()
        for bad in ((), ledger[:-1], ledger + (ledger[-1],)):
            with self.assertRaises(ValueError):
                source_air_mapping(a, bad, v, source, SOURCE.encode())
        entry = ledger[-1].entry
        ambiguous = replace(a, source_map=SourceMap(a.source_map.entries + (entry,)))
        with self.assertRaises(ValueError):
            source_air_mapping(ambiguous, ledger, v, source, SOURCE.encode())
        with self.assertRaises(ValueError):
            source_air_mapping(a, "infer by source value", v, source, SOURCE.encode())
        with self.assertRaises(ValueError):
            replace(mapping, correspondence=mapping.correspondence[:-1])
        with self.assertRaises(ValueError):
            replace(mapping, correspondence=(mapping.correspondence[0],) * 3)
        swapped = (ledger[0], replace(ledger[1], entry=ledger[2].entry), replace(ledger[2], entry=ledger[1].entry))
        forged = source_air_mapping(a, swapped, v, source, SOURCE.encode())
        with self.assertRaises(ValueError):
            forged.validate(a, ledger, v, source, SOURCE.encode())
        with self.assertRaises(ValueError):
            source_air_mapping(a, ledger, v, replace(source, logical_name="other.apex"), SOURCE.encode())

    def test_interleaved_and_nested_actions_keep_exact_order(self):
        source = """directive Main {
    state count = 0
    event tick
    cause start {
        path primary @ 10 {
            emit tick
            add count 1
            when count > 0 { set count = 2 }
            set count = 3
        }
        path secondary @ 1 { set count = 4 }
    }
}
"""
        compiled, ledger, v, governed, mapping = compiler_fixture(source)
        ordinary = compile_source_with_map(source, source_name="src/main.apex")
        self.assertEqual(compiled, ordinary)
        self.assertEqual(tuple((e.kind, e.occurrence) for e in ledger),
                         (("state", (0,)), ("assignment", (0, 0, 0)),
                          ("assignment", (0, 0, 1)), ("assignment", (0, 1, 0))))
        self.assertEqual(len(mapping.sidecar.operations), 4)
        mapping.validate(compiled, ledger, v, governed, source.encode())
        self.assertTrue(any(entry.kind == "conditional_action" for entry in compiled.source_map.entries))
        self.assertEqual(len(compiled.program.causal_decisions[0].paths[0].actions), 4)

    def test_unmapped_missing_physical_span(self):
        node = parse_source_unit(SOURCE, source_name="src/main.apex").declarations[0]
        node = replace(node, states=(replace(node.states[0], span=None),))
        ledger = []
        compiled = _compile_directive_with_map(node, operation_evidence=ledger)
        verified = AIRVerifier().verify(compiled.program).require_verified()
        mapping = source_air_mapping(compiled, tuple(ledger), verified,
            SourceIdentity.from_bytes("src/main.apex", SOURCE.encode()), SOURCE.encode())
        self.assertEqual(mapping.correspondence[0].category, "UNMAPPED")
        self.assertEqual(mapping.correspondence[0].source_map_index, -1)

    def test_stale_source_and_air_fail_closed(self):
        a, ledger, v, source, mapping = compiler_fixture()
        with self.assertRaises(ValueError):
            mapping.validate(a, ledger, v, source, SOURCE.encode() + b" ")
        changed = replace(a.program, states=(replace(a.program.states[0], initial=99),))
        changed_v = AIRVerifier().verify(changed).require_verified()
        with self.assertRaises(ValueError):
            mapping.validate(a, ledger, changed_v, source, SOURCE.encode())
        for path in ("C:/host/main.apex", "/tmp/main.apex", "../main.apex"):
            with self.assertRaises(ValueError):
                SourceIdentity.from_bytes(path, SOURCE.encode())

    def test_compiler_actions_and_admission_unchanged(self):
        a, ledger, v, source, mapping = compiler_fixture()
        actions = a.program.causal_decisions[0].paths[0].actions
        before = build_verified_air_lowering_input(v).transport_json
        mapping.validate(a, ledger, v, source, SOURCE.encode())
        self.assertTrue(actions)
        self.assertIs(actions, a.program.causal_decisions[0].paths[0].actions)
        self.assertEqual(before, build_verified_air_lowering_input(v).transport_json)
        with self.assertRaises(NativeExecutionError):
            emit_native_source_mapping(v, plan_for(a.program), source_mapping=mapping, source_contents=(SOURCE.encode(),))
        self.assertIs(actions, a.program.causal_decisions[0].paths[0].actions)

    def test_emitter_determinism_and_frozen_c_bytes(self):
        v, plan, content, mapping = native_fixture()
        other_content, other = emit_native_source_mapping(v, plan)
        self.assertEqual(content, other_content)
        self.assertEqual(mapping.regions, other.regions)
        self.assertEqual(mapping.canonical_form(), other.canonical_form())
        self.assertEqual(mapping.fingerprint(), other.fingerprint())
        admission = native.admit_native_profile(v, plan)
        self.assertEqual(content, frozen_emitter()(admission))
        self.assertEqual(content, native._source(admission))
        mapping.validate(v, plan, content)
        self.assertEqual(mapping.source_mapping_fingerprint, "UNMAPPED_SOURCE")
        self.assertEqual(len(mapping.regions), len(admission.state_ids) + len(admission.stores))
        snippets = tuple(content[r.span.start.offset:r.span.end.offset].decode() for r in mapping.regions)
        self.assertIn("volatile __int64 s0", snippets[0])
        self.assertIn("s0 = 41LL;", snippets[-2])
        self.assertIn("s0 = 42LL;", snippets[-1])
        self.assertNotEqual(mapping.regions[-2].operation.operation_id, mapping.regions[-1].operation.operation_id)

    def test_native_stale_and_substituted_provenance(self):
        v, plan, content, mapping = native_fixture()
        for raw in (content + b" ", content.replace(b"41LL", b"99LL")):
            with self.assertRaises(ValueError):
                mapping.validate(v, plan, raw)
        changed = with_path(v.program, assignments=(replace(v.program.causal_decisions[0].paths[0].assignments[0], value=99),))
        changed_v = AIRVerifier().verify(changed).require_verified()
        with self.assertRaises(ValueError):
            mapping.validate(changed_v, plan_for(changed), content)
        with self.assertRaises(ValueError):
            replace(mapping, profile="other-profile")
        with self.assertRaises(ValueError):
            replace(mapping, source_mapping_fingerprint="C:/host/debug.map")
        stale = replace(mapping, generated_source=replace(mapping.generated_source, content_fingerprint="0" * 64))
        with self.assertRaises(ValueError):
            stale.validate(v, plan, content)
        bad = replace(mapping, association=replace(mapping.association, routing_fingerprint="0" * 64))
        with self.assertRaises(ValueError):
            bad.validate(v, plan, content)
        with self.assertRaises(ValueError):
            emit_native_source_mapping(v, plan, source_contents=(b"infer missing correspondence",))
        with self.assertRaises(ValueError):
            emit_native_source_mapping(v, plan, source_mapping="infer missing correspondence")

    def test_generated_region_negatives_and_wrong_locator(self):
        v, plan, content, mapping = native_fixture()
        for regions in (mapping.regions[:-1], (mapping.regions[0],) * len(mapping.regions)):
            with self.assertRaises(ValueError):
                replace(mapping, regions=regions)
        with self.assertRaises(ValueError):
            replace(mapping, regions=(mapping.regions[0], replace(mapping.regions[1], span=mapping.regions[0].span)) + mapping.regions[2:])
        empty = SourceText("program.c", content.decode()).span(0, 0)
        with self.assertRaises(ValueError):
            GeneratedRegion(mapping.regions[0].operation, empty)
        beyond = SourceSpan("program.c", mapping.regions[-1].span.start, SourcePosition(1, len(content)+99, len(content)+98))
        forged = replace(mapping, regions=mapping.regions[:-1] + (replace(mapping.regions[-1], span=beyond),))
        with self.assertRaises(ValueError):
            forged.validate(v, plan, content)
        # Valid but wrong assignment occurrence, not a guessed best match.
        operations = list(mapping.sidecar.operations)
        left, right = operations[-2:]
        operations[-2] = OperationReference(left.ordinal, right.identity)
        operations[-1] = OperationReference(right.ordinal, left.identity)
        sidecar = replace(mapping.sidecar, operations=tuple(operations))
        association = replace(mapping.association, sidecar_fingerprint=sidecar.fingerprint())
        wrong = replace(mapping, sidecar=sidecar, association=association,
            regions=tuple(replace(r, operation=op) for r, op in zip(mapping.regions, operations)))
        with self.assertRaises(ValueError):
            wrong.validate(v, plan, content)

    def test_no_second_semantics_audit(self):
        forbidden = {"id", "eval", "exec", "resolve", "infer_type", "resolve_type", "select_path", "evaluate",
                     "execute", "compile_expression", "_type_check_directive_actions"}
        for filename in ("tooling/source_air_mapping.py", "native_backend/source_mapping.py"):
            tree = ast.parse((ROOT / "apexforge" / filename).read_text(encoding="utf-8"))
            calls = {n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id for n in ast.walk(tree)
                     if isinstance(n, ast.Call) and isinstance(n.func, (ast.Attribute, ast.Name))}
            self.assertFalse(calls & forbidden)
            imports = {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            self.assertFalse(any(x.startswith(("runtime", "type_system", "authority", "causality.engine")) for x in imports))
        a, ledger, v, source, mapping = compiler_fixture()
        with patch("runtime.engine.RuntimeEngine.execute", side_effect=AssertionError("semantic execution")), \
             patch("language.compiler.compile_source_with_map", side_effect=AssertionError("recompile inference")), \
             patch("air.verify.AIRVerifier.verify", side_effect=AssertionError("source metadata verification")):
            mapping.validate(a, ledger, v, source, SOURCE.encode())


class NativeNeutralityTests(unittest.TestCase):
    def test_live_mapped_build_preserves_image_receipt_output_result(self):
        v, plan, content, mapping = native_fixture()
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p12-6-4-", dir=build_root) as directory:
            base, mapped_dir, repeat_dir = (Path(directory) / name for name in ("base", "mapped", "repeat"))
            for path in (base, mapped_dir, repeat_dir):
                path.mkdir()
            with patch.object(native, "_source", side_effect=frozen_emitter()):
                baseline = native.build_native(v, plan, base)
            mapped = build_native_with_mapping(v, plan, mapped_dir)
            repeated = build_native_with_mapping(v, plan, repeat_dir)
            mapped.validate(v, plan)
            self.assertEqual(baseline.image.read_bytes(), mapped.artifact.image.read_bytes())
            self.assertEqual(mapped.artifact.image.read_bytes(), repeated.artifact.image.read_bytes())
            self.assertEqual(baseline.receipt_json, mapped.artifact.receipt_json)
            self.assertEqual(mapped.artifact.receipt_json, repeated.artifact.receipt_json)
            expected = native.dispatch_native(baseline, v, plan)
            actual = native.dispatch_native(mapped.artifact, v, plan)
            again = native.dispatch_native(repeated.artifact, v, plan)
            self.assertEqual(expected, actual)
            self.assertEqual(actual, again)
            self.assertEqual(mapped.mapping.fingerprint(), repeated.mapping.fingerprint())
            oracle = run_air_program(v.program, entry_directives=(plan.entry_directive,))
            self.assertEqual({x.name: int(x.data) for x in actual.result.outputs.values},
                             {x.key: x.value for x in oracle.final_state.cells})
            with self.assertRaises(ValueError):
                replace(mapped, mapping_fingerprint="0" * 64).validate(v, plan)
            with self.assertRaises(ValueError):
                replace(mapped, receipt_fingerprint="0" * 64).validate(v, plan)


if __name__ == "__main__":
    unittest.main(verbosity=2)
