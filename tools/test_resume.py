"""Small isolated regressions at the workflow/native and archive seams.

Run with: python3 -m unittest discover -s tools -p test_resume.py
Compiler scenarios require the exact installed compiler; setup supplies it in CI.
"""

import copy
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import importlib.util
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

import resume


class ArchiveSafety(unittest.TestCase):
    def test_integrity_and_unsafe_members_are_rejected_before_installation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for kind in ("tar", "zip"):
                target = "x86_64-pc-windows-msvc" if kind == "zip" else "x86_64-unknown-linux-musl"
                prefix = f"typst-{target}"
                binary = "typst.exe" if kind == "zip" else "typst"
                for fault in ("checksum", "duplicate", "link", "traversal", "oversize", "malformed"):
                    with self.subTest(kind=kind, fault=fault):
                        archive = root / (f"{kind}-{fault}.zip" if kind == "zip" else f"{kind}-{fault}.tar.xz")
                        members = [(f"{prefix}/{binary}", b"not executable"), (f"{prefix}/LICENSE", b"license"), (f"{prefix}/NOTICE", b"notice")]
                        if fault == "duplicate":
                            members.append(members[0])
                        if fault == "traversal":
                            members.insert(0, ("../outside", b"bad"))
                        if fault == "oversize":
                            # Metadata is oversized without allocating a huge payload.
                            if kind == "zip":
                                members.insert(0, (f"{prefix}/README.md", b"x" * (4 * 1024 * 1024 + 1)))
                        if fault == "malformed":
                            archive.write_bytes(b"not an archive")
                        elif kind == "zip":
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore", UserWarning)
                                with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                                    for name, data in members:
                                        info = zipfile.ZipInfo(name)
                                        info.compress_type = zipfile.ZIP_DEFLATED
                                        if fault == "link" and name.endswith(binary):
                                            info.create_system = 3
                                            info.external_attr = (stat.S_IFLNK | 0o777) << 16
                                        bundle.writestr(info, data)
                        else:
                            with tarfile.open(archive, "w:xz") as bundle:
                                if fault == "oversize":
                                    info = tarfile.TarInfo(f"{prefix}/README.md")
                                    info.size = 4 * 1024 * 1024 + 1
                                    bundle.addfile(info, io.BytesIO(b"x" * info.size))
                                else:
                                    for name, data in members:
                                        info = tarfile.TarInfo(name)
                                        if fault == "link" and name.endswith(binary):
                                            info.type = tarfile.SYMTYPE
                                            info.linkname = "../outside"
                                            bundle.addfile(info)
                                        else:
                                            info.size = len(data)
                                            bundle.addfile(info, io.BytesIO(data))
                        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
                        if fault == "checksum":
                            digest = "0" * 64
                        destination = root / f"unpack-{kind}-{fault}"
                        destination.mkdir()
                        with self.assertRaises(resume.WorkflowError):
                            resume.unpack_archive(archive, destination, target, digest)
                        self.assertFalse((root / "outside").exists())


class ShippedThemes(unittest.TestCase):
    def test_shipped_presets_keep_list_spacing_equal_to_leading(self):
        for name in ("classic", "modern"):
            theme = json.loads((resume.ROOT / "themes" / f"{name}.json").read_text(encoding="utf-8"))
            for surface in ("cv", "letter"):
                with self.subTest(theme=name, surface=surface):
                    spacing = theme[surface]["spacing"]
                    self.assertEqual(spacing["leading"], spacing["list"])


class WorkspaceScenarios(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "project"
        self.root.mkdir()
        for name in ("tools", "examples", "themes", "lib"):
            shutil.copytree(resume.ROOT / name, self.root / name, ignore=shutil.ignore_patterns("__pycache__"))
        for name in ("cv.typ", "letter.typ"):
            shutil.copyfile(resume.ROOT / name, self.root / name)

    def cli(self, *args):
        return subprocess.run([sys.executable, str(self.root / "tools" / "resume.py"), *args], cwd=self.temporary.name, capture_output=True, text=True, encoding="utf-8", errors="replace")

    def require_compiler(self):
        compiler = resume.discover_compiler()
        if compiler is None:
            self.skipTest("Run tools/resume.py setup to exercise native compiler scenarios.")
        return str(compiler)

    def write_json(self, relative, data):
        (self.root / relative).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_init_does_not_overwrite_or_merge_an_existing_workspace(self):
        self.assert_ok(self.cli("init"))
        profile = self.root / "workspace" / "profile.json"
        profile.write_text("human edits", encoding="utf-8")
        (self.root / "workspace" / "applications" / "research.json").unlink()
        result = self.cli("init")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(profile.read_text(encoding="utf-8"), "human edits")
        self.assertFalse((self.root / "workspace" / "applications" / "research.json").exists())

    def test_native_guards_and_failed_selected_build_preserve_prior_outputs(self):
        compiler = self.require_compiler()
        self.assert_ok(self.cli("init"))
        build = ("build", "--typst", compiler, "--document", "both")
        self.assert_ok(self.cli(*build))
        originals = {path: path.read_bytes() for path in (self.root / "build").rglob("*.pdf")}
        self.assertEqual(len(originals), 2)
        profile = json.loads((self.root / "workspace" / "profile.json").read_text(encoding="utf-8"))
        application = json.loads((self.root / "workspace" / "applications" / "general.json").read_text(encoding="utf-8"))
        claim_id = next(key for key, value in profile["claims"].items() if value["approved"] and "cv" in value["surfaces"])
        selected = copy.deepcopy(application)
        selected["summary"] = [claim_id]
        self.write_json("workspace/applications/general.json", selected)
        cases = []
        unapproved = copy.deepcopy(profile)
        unapproved["claims"][claim_id]["approved"] = False
        cases.append(unapproved)
        incompatible = copy.deepcopy(profile)
        incompatible["claims"][claim_id]["surfaces"] = ["letter"]
        cases.append(incompatible)
        missing = copy.deepcopy(profile)
        missing["claims"][claim_id]["evidence"] = ["missing-source"]
        cases.append(missing)
        fictional = copy.deepcopy(profile)
        fictional["is_example"] = False
        for source_id in fictional["claims"][claim_id]["evidence"]:
            fictional["sources"][source_id]["kind"] = "example"
        cases.append(fictional)
        for index, invalid in enumerate(cases):
            with self.subTest(guard=index):
                self.write_json("workspace/profile.json", invalid)
                self.assertNotEqual(self.cli(*build).returncode, 0)
                for path, original in originals.items():
                    self.assertEqual(path.read_bytes(), original)
        self.write_json("workspace/profile.json", profile)
        broken_letter = copy.deepcopy(application)
        broken_letter["letter"]["paragraphs"] = [{"text": "PRIVATE_CANDIDATE_SENTINEL", "claim_refs": []}]
        self.write_json("workspace/applications/general.json", broken_letter)
        failed = self.cli(*build)
        self.assertNotEqual(failed.returncode, 0)
        self.assertNotIn("PRIVATE_CANDIDATE_SENTINEL", failed.stderr)
        for path, original in originals.items():
            self.assertEqual(path.read_bytes(), original)
        # IDs are output paths: reject traversal, Unicode, malformed and overlong slugs.
        for bad_id in ("../escape", "A", "a--b", "résumé", "a" * 65):
            selected["id"] = bad_id
            self.write_json("workspace/applications/general.json", selected)
            self.assertNotEqual(self.cli(*build).returncode, 0)
        self.assertFalse((self.root / "escape.pdf").exists())

    def test_multipage_preview_shrinks_without_stale_pages_or_unrelated_changes(self):
        compiler = self.require_compiler()
        self.assert_ok(self.cli("init"))
        application = json.loads((self.root / "workspace" / "applications" / "general.json").read_text(encoding="utf-8"))
        profile = json.loads((self.root / "workspace" / "profile.json").read_text(encoding="utf-8"))
        theme = json.loads((self.root / "workspace" / "theme.json").read_text(encoding="utf-8"))
        claim_id = next(key for key, value in profile["claims"].items() if value["approved"] and "cv" in value["surfaces"])
        profile["claims"][claim_id]["text"] = "A fictional bounded statement supporting this demonstration."
        profile["claims"][claim_id]["qualifier"] = ""
        expanded = []
        for index in range(60):
            selected_id = f"evidence-{index}"
            profile["claims"][selected_id] = {
                **profile["claims"][claim_id],
                "text": f"Documented research question {index + 1}, its evidence and methodological limitations for the fictional study.",
            }
            expanded.append(selected_id)
        self.write_json("workspace/profile.json", profile)
        application["summary"] = []
        original = copy.deepcopy(application)
        original["sections"] = [{"title": "Brief evidence", "kind": "paragraphs", "items": [claim_id]}]
        application["sections"] = [{"title": "Extended evidence", "kind": "paragraphs", "items": expanded}]
        theme["cv"]["max_pages"] = None
        self.write_json("workspace/applications/general.json", application)
        self.write_json("workspace/theme.json", theme)
        build = ("build", "--typst", compiler, "--preview")
        self.assert_ok(self.cli(*build))
        directory = self.root / "build" / "resumes"
        old_pages = set(directory.glob(f"resume-{application['id']}-page-*.png"))
        self.assertGreater(len(old_pages), 1)
        unrelated = directory / "resume-unrelated.pdf"
        unrelated.write_bytes(b"leave this output alone")
        self.write_json("workspace/applications/general.json", original)
        self.assert_ok(self.cli(*build))
        new_pages = set(directory.glob(f"resume-{application['id']}-page-*.png"))
        self.assertEqual(len(new_pages), 1)
        self.assertTrue(new_pages < old_pages)
        self.assertEqual(unrelated.read_bytes(), b"leave this output alone")
        # A publication lock fails instead of racing an existing build.
        (self.root / "build" / ".publish-lock").mkdir()
        result = self.cli(*build)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(set(directory.glob(f"resume-{application['id']}-page-*.png")), new_pages)

    def test_page_reporting_matches_produced_pages_and_theme_limit(self):
        compiler = self.require_compiler()
        self.assert_ok(self.cli("init"))
        application = json.loads((self.root / "workspace" / "applications" / "general.json").read_text(encoding="utf-8"))
        profile = json.loads((self.root / "workspace" / "profile.json").read_text(encoding="utf-8"))
        theme = json.loads((self.root / "workspace" / "theme.json").read_text(encoding="utf-8"))
        identifier = application["id"]
        bounded = self.cli("build", "--typst", compiler, "--report-pages")
        self.assert_ok(bounded)
        claim_id = next(key for key, value in profile["claims"].items() if value["approved"] and "cv" in value["surfaces"])
        profile["claims"][claim_id]["qualifier"] = ""
        expanded = []
        for index in range(60):
            selected_id = f"evidence-{index}"
            profile["claims"][selected_id] = {
                **profile["claims"][claim_id],
                "text": f"Documented research question {index + 1}, its evidence and methodological limitations for the fictional study.",
            }
            expanded.append(selected_id)
        self.write_json("workspace/profile.json", profile)
        application["summary"] = []
        application["sections"] = [{"title": "Extended evidence", "kind": "paragraphs", "items": expanded}]
        theme["cv"]["max_pages"] = None
        self.write_json("workspace/applications/general.json", application)
        self.write_json("workspace/theme.json", theme)
        unbounded = self.cli("build", "--typst", compiler, "--preview", "--report-pages")
        self.assert_ok(unbounded)

        def reported(result, stem):
            prefix = f"{stem}.pdf:"
            line = next((line for line in result.stdout.splitlines() if line.startswith(prefix)), None)
            self.assertIsNotNone(line, f"no page report for {stem}: {result.stdout!r}")
            return [int(number) for number in re.findall(r"\d+", line[len(prefix):])]

        # An unlimited document must report exactly the pages the compiler actually produced.
        produced = sorted((self.root / "build" / "resumes").glob(f"resume-{identifier}-page-*.png"))
        self.assertGreater(len(produced), 1)
        self.assertEqual(reported(unbounded, f"resume-{identifier}"), [len(produced)])
        # A limited document must report the final page count and the enforced limit.
        self.assertEqual(reported(bounded, f"resume-{identifier}"), [1, 1])

    def test_failed_publication_and_restore_keep_previous_documents_recoverable(self):
        compiler = self.require_compiler()
        self.assert_ok(self.cli("init"))
        self.assert_ok(self.cli("build", "--typst", compiler))
        previous = self.root / "build" / "resumes" / "resume-general.pdf"
        original = previous.read_bytes()
        profile = json.loads((self.root / "workspace" / "profile.json").read_text(encoding="utf-8"))
        application = json.loads((self.root / "workspace" / "applications" / "general.json").read_text(encoding="utf-8"))
        selected_id = application["summary"][0]
        profile["claims"][selected_id]["text"] = "Changed fictional evidence for a subsequent application build."
        self.write_json("workspace/profile.json", profile)

        specification = importlib.util.spec_from_file_location("isolated_resume", self.root / "tools" / "resume.py")
        workflow = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(workflow)
        real_replace = Path.replace

        def fail_after_old_files_move(source, destination):
            if source.parent.resolve() == previous.parent.resolve():
                return real_replace(source, destination)
            raise OSError("Filesystem refused publication or restoration")

        diagnostics = io.StringIO()
        with patch.object(Path, "replace", fail_after_old_files_move), \
                patch.object(Path, "rename", side_effect=OSError("Filesystem refused recovery relocation")), \
                redirect_stdout(io.StringIO()), redirect_stderr(diagnostics):
            status = workflow.main(["build", "--typst", compiler])

        self.assertNotEqual(status, 0)
        recoverable = [path for path in (self.root / "build").rglob("*.pdf") if path.read_bytes() == original]
        self.assertTrue(recoverable, "Prior document bytes must survive failed restoration and recovery relocation.")
        self.assertTrue(any(str(path.parent.resolve()) in diagnostics.getvalue() for path in recoverable))


if __name__ == "__main__":
    unittest.main()
