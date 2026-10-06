"""P16.5 archive contracts; fixtures are not claims of local release builds."""
import ast
import base64
import csv
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from io import BytesIO, StringIO
from pathlib import Path
import gzip
import sys
import tarfile
import unittest
from unittest.mock import patch
import zipfile
import warnings
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tooling import python_distribution as p
from tooling import release_architecture as r
from tooling import release_build as b
from tooling import release_manifest as m

PROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def identity():
    metadata = p.PythonProjectMetadata(PROJECT.read_bytes())
    return p.PythonDistributionIdentity(r.ReleaseIdentity("python-review", "declared-release-16", "DEVELOPMENT", r.P15_BASELINE),
                                      "apexforge-language", "10.1.3", metadata)


def metadata_bytes(version="10.1.3", requirement=">=3.9"):
    return ("Metadata-Version: 2.1\nName: apexforge-language\nVersion: " + version +
            "\nSummary: ApexForge language, runtime, and project tooling\nRequires-Python: " + requirement + "\n\n").encode("utf-8")


def wheel_files():
    stem = "apexforge_language-10.1.3.dist-info/"
    return {"tooling/__init__.py": b"", "tooling/cli.py": b"raise Exception('never execute')\n",
            stem + "METADATA": metadata_bytes(), stem + "WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
            stem + "entry_points.txt": b"[console_scripts]\napexforge = tooling.cli:main\n"}


def wheel_bytes(files=None, timestamp=(2000, 1, 1, 0, 0, 0), record=True):
    files = dict(wheel_files() if files is None else files)
    rp = "apexforge_language-10.1.3.dist-info/RECORD"
    if record:
        stream = StringIO(newline="")
        writer = csv.writer(stream)
        for name, data in sorted(files.items()):
            writer.writerow((name, "sha256=" + base64.urlsafe_b64encode(sha256(data).digest()).rstrip(b"=").decode(), str(len(data))))
        writer.writerow((rp, "", ""))
        files[rp] = stream.getvalue().encode()
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in files.items():
            archive.writestr(zipfile.ZipInfo(name, timestamp), data)
    return buffer.getvalue()


def sdist_bytes(extra=(), timestamp=1000):
    files = {"PKG-INFO": metadata_bytes(), "pyproject.toml": PROJECT.read_bytes(),
             "apexforge/tooling/__init__.py": b"", "apexforge/tooling/cli.py": b"raise Exception('never execute')\n"}
    root = "apexforge-language-10.1.3/"
    raw = BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name, data in tuple((root + k, v) for k, v in files.items()) + tuple(extra):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mtime = timestamp
            archive.addfile(info, BytesIO(data))
    return gzip.compress(raw.getvalue(), mtime=timestamp)


def evidence(kind="wheel", data=None):
    ident = identity()
    filename = "apexforge_language-10.1.3-py3-none-any.whl" if kind == "wheel" else "apexforge-language-10.1.3.tar.gz"
    descriptor = r.ReleaseArtifactDescriptor(ident.release, r.ReleaseArtifactIdentity("python-" + kind), r.ReleaseTarget("python"),
                    "PYTHON_DISTRIBUTION", kind, filename, ident.version, "SUPPORTED")
    return p.PythonPackageEvidence(ident, descriptor, (wheel_bytes() if kind == "wheel" else sdist_bytes()) if data is None else data)


class ContractTests(unittest.TestCase):
    def error(self, code, callback):
        with self.assertRaises(p.PythonDistributionError) as caught:
            callback()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(str(caught.exception), code)

    def test_models_immutable(self):
        x = evidence()
        for obj in (x.identity, x.identity.metadata, x, p.PythonReproducibilityEvidence(x, evidence())):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, next(iter(obj.__dataclass_fields__)), None)

    def test_exact_repository_metadata_projection(self):
        record = identity().metadata.record()
        self.assertEqual(record["project"]["name"], "apexforge-language")
        self.assertEqual(record["project"]["version"], "10.1.3")
        self.assertEqual(record["project"]["requires-python"], ">=3.9")
        self.assertEqual(record["build_system"], {"requires": ["setuptools>=61"], "build-backend": "setuptools.build_meta"})
        self.assertEqual(record["setuptools"], {"package-dir": {"": "apexforge"}, "include-package-data": False, "packages": {"find": {"where": ["apexforge"]}}})
        self.assertEqual(record["project"]["dependencies"], [])
        self.assertEqual(record["project"]["scripts"], {"apexforge": "tooling.cli:main"})
        for key in ("readme", "license", "optional_dependencies", "package_data"):
            self.assertIsNone(record[key])

    def test_metadata_changes_not_silently_accepted(self):
        self.error("PYTHON_PROJECT_METADATA_MISMATCH", lambda: p.PythonProjectMetadata(PROJECT.read_bytes().replace(b"10.1.3", b"16.5.0")))

    def test_release_and_version_domains_distinct(self):
        x = identity()
        self.assertNotEqual(x.release.version, x.version)
        self.assertEqual(x.release.baseline, r.P15_BASELINE)
        self.assertNotEqual(x.fingerprint(), replace(x, release=replace(x.release, version="another-release")).fingerprint())
        self.error("PYTHON_IDENTITY_METADATA_MISMATCH", lambda: replace(x, version=x.release.version))

    def test_wrong_identity_or_baseline_rejected(self):
        x = identity()
        self.error("PYTHON_IDENTITY_METADATA_MISMATCH", lambda: replace(x, name="ApexForge-Language"))
        self.error("PYTHON_RELEASE_BINDING_INVALID", lambda: replace(x, release=replace(x.release, baseline=replace(r.P15_BASELINE, commit="a" * 40))))

    def test_wheel_and_sdist_byte_backed(self):
        for kind in ("wheel", "sdist"):
            x = evidence(kind)
            self.assertEqual(x.record()["length"], len(x.data))
            self.assertEqual(x.record()["digest"], p.digest(x.data))
            self.assertTrue(x._inventory)

    def test_descriptor_binding_exact(self):
        x = evidence()
        self.error("PYTHON_PACKAGE_BINDING_INVALID", lambda: replace(x, descriptor=replace(x.descriptor, surface_version="10.1.4")))
        self.error("PYTHON_PACKAGE_BINDING_INVALID", lambda: replace(x, descriptor=replace(x.descriptor, release=replace(x.identity.release, version="other"))))

    def test_wheel_filename_metadata_agreement(self):
        x = evidence()
        self.error("PYTHON_WHEEL_FILENAME_MISMATCH", lambda: replace(x, descriptor=replace(x.descriptor, filename="other-10.1.3-py3-none-any.whl")))

    def test_wheel_core_metadata_exact(self):
        files = wheel_files()
        for data in (metadata_bytes("10.1.4"), metadata_bytes(requirement=">=3.10"), metadata_bytes() + b"Name: wrong\n"):
            # The final case is body text; duplicate headers are tested separately.
            if data.endswith(b"Name: wrong\n"):
                data = metadata_bytes().replace(b"Name: apexforge-language", b"Name: apexforge-language\nName: wrong")
            files["apexforge_language-10.1.3.dist-info/METADATA"] = data
            self.error("PYTHON_METADATA_MISMATCH", lambda: evidence(data=wheel_bytes(files)))

    def test_wheel_required_metadata_files(self):
        for suffix in ("METADATA", "WHEEL", "entry_points.txt"):
            files = wheel_files()
            del files["apexforge_language-10.1.3.dist-info/" + suffix]
            self.error("PYTHON_WHEEL_METADATA_MISSING", lambda: evidence(data=wheel_bytes(files)))
        self.error("PYTHON_WHEEL_METADATA_MISSING", lambda: evidence(data=wheel_bytes(record=False)))

    def test_wheel_tags_and_entry_points(self):
        files = wheel_files()
        files["apexforge_language-10.1.3.dist-info/WHEEL"] = b"Wheel-Version: 2.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
        self.error("PYTHON_WHEEL_TAG_MISMATCH", lambda: evidence(data=wheel_bytes(files)))
        files = wheel_files()
        files["apexforge_language-10.1.3.dist-info/entry_points.txt"] = b"[console_scripts]\napexforge = hostile:main\n"
        self.error("PYTHON_ENTRY_POINTS_MISMATCH", lambda: evidence(data=wheel_bytes(files)))

    def test_record_hash_and_length_integrity(self):
        data = wheel_bytes()
        members, _ = p.wheel_members(data)
        rp = "apexforge_language-10.1.3.dist-info/RECORD"
        members["tooling/cli.py"] += b"changed"
        self.error("PYTHON_WHEEL_RECORD_MISMATCH", lambda: p.wheel_record(members, rp))

    def test_record_coverage_and_duplicates(self):
        members, _ = p.wheel_members(wheel_bytes())
        rp = "apexforge_language-10.1.3.dist-info/RECORD"
        members[rp] += members[rp].splitlines(keepends=True)[0]
        self.error("PYTHON_WHEEL_RECORD_INVALID", lambda: p.wheel_record(members, rp))

    def test_sdist_metadata_and_safe_paths(self):
        self.assertTrue(evidence("sdist")._inventory)
        for name in ("../hostile.py", "/absolute.py", "C:/drive.py", "root/../escape.py", "root\\hostile.py"):
            self.error("PYTHON_ARCHIVE_PATH_INVALID", lambda: evidence("sdist", sdist_bytes(((name, b"data"),))))

    def test_wheel_safe_paths(self):
        for name in ("../hostile.py", "/absolute.py", "C:/drive.py", "bad\\name.py"):
            files = wheel_files()
            files[name] = b"data"
            self.error("PYTHON_ARCHIVE_PATH_INVALID", lambda: evidence(data=wheel_bytes(files)))

    def test_duplicate_archive_path_rejected(self):
        self.error("PYTHON_ARCHIVE_DUPLICATE", lambda: evidence("sdist", sdist_bytes((("apexforge-language-10.1.3/PKG-INFO", b"different"),))))
        raw = BytesIO(wheel_bytes())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(raw, "a") as archive:
                archive.writestr("tooling/cli.py", b"different")
        self.error("PYTHON_ARCHIVE_DUPLICATE", lambda: evidence(data=raw.getvalue()))
        files = wheel_files()
        files["TOOLING/CLI.py"] = b"case alias"
        self.error("PYTHON_ARCHIVE_DUPLICATE", lambda: evidence(data=wheel_bytes(files)))
        files = wheel_files()
        files["tooling"] = b"file cannot also be directory"
        self.error("PYTHON_ARCHIVE_ENTRY_INVALID", lambda: evidence(data=wheel_bytes(files)))

    def test_generated_residue_rejected(self):
        for name in ("tooling/__pycache__/x.pyc", "tooling/x.pyc", "build/result.py", "dist/old.whl", "tooling/secrets"):
            files = wheel_files()
            files[name] = b"data"
            self.error("PYTHON_PACKAGE_RESIDUE", lambda: evidence(data=wheel_bytes(files)))
        files = wheel_files()
        files[".git/config"] = b"data"
        self.error("PYTHON_ARCHIVE_PATH_INVALID", lambda: evidence(data=wheel_bytes(files)))
        files = wheel_files()
        files["tooling/.env"] = b"data"
        self.error("PYTHON_ARCHIVE_PATH_INVALID", lambda: evidence(data=wheel_bytes(files)))

    def test_symlink_archive_rejected(self):
        raw = BytesIO(wheel_bytes())
        with zipfile.ZipFile(raw, "a") as archive:
            info = zipfile.ZipInfo("tooling/link.py")
            info.external_attr = 0o120777 << 16
            archive.writestr(info, b"target")
        self.error("PYTHON_ARCHIVE_ENTRY_INVALID", lambda: evidence(data=raw.getvalue()))
        raw = BytesIO()
        with tarfile.open(fileobj=raw, mode="w") as archive:
            info = tarfile.TarInfo("apexforge-language-10.1.3/link")
            info.type = tarfile.SYMTYPE
            info.linkname = "../escape"
            archive.addfile(info)
        self.error("PYTHON_ARCHIVE_ENTRY_INVALID", lambda: evidence("sdist", gzip.compress(raw.getvalue(), mtime=0)))

    def test_malformed_archives_rejected(self):
        self.error("PYTHON_WHEEL_INVALID", lambda: evidence(data=b"not zip"))
        self.error("PYTHON_SDIST_INVALID", lambda: evidence("sdist", b"not gzip"))

    def test_metadata_utf8_and_size_bounds(self):
        self.error("PYTHON_METADATA_TEXT_INVALID", lambda: p.core_metadata(b"\xff", identity()))
        self.error("PYTHON_METADATA_SIZE_INVALID", lambda: p.core_metadata(b"x" * (p.MAX_METADATA + 1), identity()))
        self.error("PYTHON_ARCHIVE_SIZE_INVALID", lambda: p.wheel_members(b"x" * (p.MAX_ARCHIVE + 1)))
        self.error("PYTHON_WHEEL_RECORD_INVALID", lambda: p.wheel_record({"oversized": b"x" * (p.MAX_MEMBER + 1)}, "RECORD"))

    def test_expected_owner_source_contents(self):
        x = evidence()
        expected = tuple((name, value) for name, _, value in x._inventory if name.endswith(".py"))
        self.assertEqual(replace(x, expected_sources=expected).expected_sources, expected)
        self.error("PYTHON_PACKAGE_SOURCE_MISMATCH", lambda: replace(x, expected_sources=(("tooling/cli.py", "A" * 64),)))

    def test_independent_content_and_raw_reproducibility(self):
        a, z = evidence(), evidence()
        self.assertIsNot(a, z)
        self.assertEqual(a.fingerprint(), z.fingerprint())
        self.assertEqual(p.PythonReproducibilityEvidence(a, z).record()["raw_bytes"], "PASS")

    def test_timestamp_difference_does_not_become_raw_reproducibility(self):
        for kind, data in (("wheel", wheel_bytes(timestamp=(2020, 1, 1, 0, 0, 0))), ("sdist", sdist_bytes(timestamp=2000))):
            result = p.PythonReproducibilityEvidence(evidence(kind), evidence(kind, data)).record()
            self.assertEqual(result["content"], "PASS")
            self.assertEqual(result["raw_bytes"], "MISMATCH")
            self.assertEqual(result["finding"], "PYTHON_PACKAGE_BYTE_REPRODUCIBILITY_GAP")

    def test_changed_contents_not_reproducible(self):
        files = wheel_files()
        files["tooling/cli.py"] = b"different code as data"
        result = p.PythonReproducibilityEvidence(evidence(), evidence(data=wheel_bytes(files))).record()
        self.assertEqual(result["content"], "MISMATCH")

    def test_generic_build_and_manifest_integration(self):
        x = evidence()
        artifact, checksum = p.generic_evidence(x)
        self.assertEqual(artifact.data, x.data)
        self.assertEqual(checksum.digest, p.digest(x.data))
        self.assertEqual(artifact.recipe.inputs[0].source.fingerprint, x.fingerprint())
        self.assertIn(x.identity.fingerprint(), artifact.canonical_json())
        matrix = r.ReleaseArtifactMatrix(x.identity.release, (x.descriptor,))
        artifacts = b.ReleaseArtifactSet(x.identity.release, (artifact.recipe,), (artifact,))
        sums = m.ReleaseChecksumSet(x.identity.release, m.reference(matrix), (checksum,))
        records = tuple(m.ReleaseProvenanceRecord("owner-" + str(i), x.identity.release, kind, subject, predecessors)
                        for i, (kind, subject, predecessors) in enumerate(m.required_lineage(matrix, artifacts, sums)))
        result = m.ReleaseManifest(matrix, artifacts, sums, m.ReleaseProvenanceBundle(x.identity.release, records))
        self.assertEqual(result.status, "COMPLETE")

    def test_no_authority_trust_compatibility_signing_install_publication(self):
        record = evidence().record()
        for key in ("authority", "trusted", "authenticated", "installed", "published"):
            self.assertFalse(record[key])
        self.assertEqual(record["compatibility"], "NOT_ESTABLISHED")
        self.assertEqual(record["crypto"], "CRYPTO_PROVIDER_UNAVAILABLE")
        self.assertEqual(record["semantic_authority"], "CANONICAL_AIR")

    def test_no_package_code_execution_during_inspection(self):
        with patch.object(p.subprocess, "run", side_effect=AssertionError("no tool during inspection")):
            self.assertTrue(evidence().fingerprint())
            self.assertTrue(evidence("sdist").fingerprint())

    def test_fixed_backend_command_and_cleanup(self):
        meta = identity().metadata
        sources = (("pyproject.toml", meta.pyproject),)
        observed = []
        def runner(argv, **kwargs):
            observed.append(kwargs["cwd"].parent)
            self.assertEqual(argv[:4], [sys.executable, "-I", "-B", "-c"])
            self.assertFalse(kwargs["shell"])
            self.assertEqual(kwargs["timeout"], 120)
            self.assertEqual(kwargs["env"]["PIP_NO_INDEX"], "1")
            self.assertTrue(Path(kwargs["env"]["USERPROFILE"]).is_relative_to(kwargs["cwd"].parent))
            self.assertEqual(set(kwargs["env"]) - {"SystemRoot"}, {"PIP_NO_INDEX", "PIP_DISABLE_PIP_VERSION_CHECK", "PYTHONDONTWRITEBYTECODE", "HOME", "USERPROFILE", "TEMP", "TMP"})
            self.assertNotIn("pip install", argv[-1])
            (kwargs["cwd"].parent / "output" / "project.tar.gz").write_bytes(b"actual output bytes")
            return p.subprocess.CompletedProcess(argv, 0, b"", b"")
        with patch.object(p.subprocess, "run", side_effect=runner):
            self.assertEqual(p.build_local(meta, sources, "sdist"), ("project.tar.gz", b"actual output bytes"))
        self.assertTrue(all(not root.exists() for root in observed))

    def test_missing_tool_dependency_classified_no_install(self):
        with patch.object(p.subprocess, "run", return_value=p.subprocess.CompletedProcess([], 1, b"", b"invalid command 'bdist_wheel'")):
            self.error("PYTHON_BUILD_ENVIRONMENT_DEPENDENCY", lambda: p.build_local(identity().metadata, (("pyproject.toml", PROJECT.read_bytes()),), "wheel"))

    def test_linked_build_output_rejected(self):
        def runner(argv, **kwargs):
            (kwargs["cwd"].parent / "output" / "project.tar.gz").write_bytes(b"data")
            return p.subprocess.CompletedProcess(argv, 0, b"", b"")
        with patch.object(p.subprocess, "run", side_effect=runner), patch.object(Path, "is_symlink", return_value=True):
            self.error("PYTHON_BUILD_OUTPUT_INVALID", lambda: p.build_local(identity().metadata, (("pyproject.toml", PROJECT.read_bytes()),), "sdist"))

    def test_no_arbitrary_commands_or_setup_code(self):
        meta = identity().metadata
        for kind in ("npm", "pip install", lambda: True):
            self.error("PYTHON_BUILD_REQUEST_INVALID", lambda: p.build_local(meta, (), kind))
        self.error("PYTHON_BUILD_SOURCE_INVALID", lambda: p.build_local(meta, (("setup.py", b"code"),), "sdist"))
        self.error("PYTHON_BUILD_SOURCE_INVALID", lambda: p.build_local(meta, (("SETUP.PY", b"code"),), "sdist"))
        self.error("PYTHON_BUILD_SOURCE_INVALID", lambda: p.build_local(meta, (("pyproject.toml", meta.pyproject), ("PYPROJECT.TOML", b"override")), "sdist"))
        self.error("PYTHON_BUILD_SOURCE_INVALID", lambda: p.build_local(meta, (("../escape", b"code"),), "sdist"))

    def test_static_security_audit(self):
        tree = ast.parse(Path(p.__file__).read_text(encoding="utf-8"))
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                self.assertNotIn(name, ("eval", "exec", "__import__", "extractall", "extract", "getenv", "system", "popen"))
                if name == "run":
                    calls.append(node)
            if isinstance(node, ast.Import):
                self.assertTrue(all(a.name not in ("socket", "requests", "urllib", "http", "pickle", "keyring") for a in node.names))
        self.assertEqual(len(calls), 1)

    def test_nonfinite_archive_timestamp_rejected(self):
        raw = BytesIO()
        with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as archive:
            info = tarfile.TarInfo("apexforge-language-10.1.3/PKG-INFO")
            info.size = 0
            info.pax_headers = {"mtime": "nan"}
            archive.addfile(info, BytesIO(b""))
        self.error("PYTHON_ARCHIVE_METADATA_INVALID", lambda: evidence("sdist", gzip.compress(raw.getvalue(), mtime=0)))

    def test_hostile_caller_objects_not_evaluated(self):
        class Hostile:
            def __len__(self):
                raise AssertionError("must not run")
        self.error("PYTHON_ARCHIVE_SIZE_INVALID", lambda: p.wheel_members(Hostile()))
        self.error("PYTHON_BUILD_SOURCE_INVALID", lambda: p.build_local(identity().metadata, (Hostile(),), "sdist"))
        self.error("PYTHON_METADATA_BINDING_INVALID", lambda: p.core_metadata(metadata_bytes(), Hostile()))
        self.error("PYTHON_WHEEL_RECORD_INVALID", lambda: p.wheel_record(Hostile(), "RECORD"))
        self.error("PYTHON_SDIST_ROOT_INVALID", lambda: p.sdist_members(sdist_bytes(), Hostile()))

    def test_metadata_provider_unavailable_is_explicit(self):
        with patch.object(p, "tomllib", None):
            self.error("PYTHON_METADATA_ENVIRONMENT_DEPENDENCY", lambda: p.PythonProjectMetadata(PROJECT.read_bytes()))


if __name__ == "__main__":
    unittest.main()
