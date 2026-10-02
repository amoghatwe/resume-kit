#!/usr/bin/env python3
"""Local, stdlib-only workflow for editable JSON and native Typst documents."""

import argparse
from contextlib import contextmanager
import hashlib
import json
import lzma
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import zlib

ROOT = Path(__file__).resolve().parent.parent
VERSION = "0.15.1"
MAX_ARCHIVE = 128 * 1024 * 1024
MAX_UNPACKED = 256 * 1024 * 1024
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.ASCII)


class WorkflowError(Exception):
    """A useful diagnostic that contains no candidate document contents."""


def read_json(path):
    try:
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}.") from exc
    except UnicodeError as exc:
        raise WorkflowError(f"Expected UTF-8 JSON in {path}.") from exc


def application_id(path):
    data = read_json(path)
    value = data.get("id") if isinstance(data, dict) else None
    if not isinstance(value, str) or len(value) > 64 or not SLUG.fullmatch(value):
        raise WorkflowError("Application id must be 1–64 ASCII lowercase letters/digits, separated by single hyphens.")
    return value


def input_path(value, directory=False):
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve(strict=True)
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise WorkflowError("Input paths must resolve inside the project root.") from exc
    if not (path.is_dir() if directory else path.is_file()):
        raise WorkflowError(f"Expected {'directory' if directory else 'file'}: {path}")
    return path


def safe_destination(path):
    """Reject symlinks, Windows junctions/reparse points and redirected ancestors."""
    path = Path(path)
    try:
        relative = path.relative_to(ROOT)
    except ValueError as exc:
        raise WorkflowError("Output/install paths must be inside the project root.") from exc
    if any(part in (".", "..") for part in relative.parts):
        raise WorkflowError("Output/install paths cannot contain traversal segments.")
    current = ROOT
    for part in relative.parts:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise WorkflowError(f"Refusing redirected output/install path: {current}")
        if current.resolve() != current:
            raise WorkflowError(f"Refusing redirected output/install ancestor: {current}")
    return path


@contextmanager
def exclusive_lock(path):
    safe_destination(path)
    try:
        path.mkdir()
    except FileExistsError as exc:
        raise WorkflowError(f"Another operation holds {path}. If a previous process crashed, remove this lock only after checking it is no longer running.") from exc
    try:
        yield
    finally:
        path.rmdir()


@contextmanager
def transaction_stage(parent, prefix):
    """Keep prior files recoverable when a filesystem failure prevents rollback."""
    stage = Path(tempfile.mkdtemp(prefix=prefix, dir=parent))
    try:
        yield stage
    except BaseException:
        remaining = []
        for name in ("backup", "old"):
            backup = stage / name
            try:
                if backup.exists() and (not backup.is_dir() or any(backup.iterdir())):
                    remaining.append(backup)
            except OSError:
                remaining.append(backup)
        if remaining:
            print("Recovery data retained at " + ", ".join(map(str, remaining)), file=sys.stderr)
        else:
            shutil.rmtree(stage)
        raise
    else:
        shutil.rmtree(stage)


def binary_name():
    return "typst.exe" if platform.system() == "Windows" else "typst"


def local_binary():
    return ROOT / ".tools" / f"typst-{VERSION}" / binary_name()


def exact_compiler(path):
    try:
        result = subprocess.run([str(path), "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and re.fullmatch(r"typst 0\.15\.1(?:\s+\([^\r\n]*\))?\s*", result.stdout) is not None


def explicit_compiler(value):
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve(strict=True)
    if not path.is_file() or not exact_compiler(path):
        raise WorkflowError(f"Explicit compiler must be an executable Typst {VERSION}: {path}")
    return path


def discover_compiler(explicit=None, local_only=False):
    if explicit:
        return explicit_compiler(explicit)
    local = safe_destination(local_binary())
    candidates = [local]
    if not local_only:
        on_path = shutil.which("typst")
        if on_path:
            candidates.append(Path(on_path))
        candidates.extend([Path("/opt/homebrew/bin/typst"), Path("/usr/local/bin/typst")])
    for candidate in candidates:
        if candidate.is_file() and exact_compiler(candidate):
            return candidate.resolve()
    return None


def platform_target():
    system = platform.system()
    machine = platform.machine().lower()
    aliases = {"arm64": "aarch64", "arm64e": "aarch64", "amd64": "x86_64", "x64": "x86_64", "x86-64": "x86_64", "armv7l": "armv7", "armv7a": "armv7", "riscv64": "riscv64gc"}
    machine = aliases.get(machine, machine)
    suffixes = {"Darwin": "apple-darwin", "Linux": "unknown-linux-musl", "Windows": "pc-windows-msvc"}
    suffix = suffixes.get(system)
    if system == "Linux" and machine == "armv7":
        suffix = "unknown-linux-musleabi"
    elif system == "Linux" and machine == "riscv64gc":
        suffix = "unknown-linux-gnu"
    target = f"{machine}-{suffix}" if suffix else None
    supported = {
        "aarch64-apple-darwin", "x86_64-apple-darwin",
        "aarch64-unknown-linux-musl", "x86_64-unknown-linux-musl",
        "armv7-unknown-linux-musleabi", "riscv64gc-unknown-linux-gnu",
        "aarch64-pc-windows-msvc", "x86_64-pc-windows-msvc",
    }
    if target not in supported:
        raise WorkflowError(f"No pinned release for {system}/{machine}. Supply a compatible Typst {VERSION} with --typst PATH; setup cannot install this platform.")
    return target


class HTTPSRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme != "https":
            raise WorkflowError("Refusing a non-HTTPS compiler download redirect.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_archive(url, destination):
    if urllib.parse.urlsplit(url).scheme != "https":
        raise WorkflowError("Compiler downloads require HTTPS.")
    opener = urllib.request.build_opener(HTTPSRedirects())
    request = urllib.request.Request(url, headers={"User-Agent": "resume-kit-bootstrap"})
    with opener.open(request, timeout=60) as response, destination.open("xb") as output:
        if urllib.parse.urlsplit(response.geturl()).scheme != "https":
            raise WorkflowError("Compiler download left HTTPS.")
        length = response.headers.get("Content-Length")
        if length and (not length.isdecimal() or int(length) > MAX_ARCHIVE):
            raise WorkflowError("Compiler archive is too large or has an invalid size.")
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_ARCHIVE:
                raise WorkflowError("Compiler archive exceeds the download size limit.")
            output.write(chunk)


def unpack_archive(archive, destination, target, expected_hash):
    """Verify first; copy exact regular members, never extract archive paths."""
    if archive.stat().st_size > MAX_ARCHIVE:
        raise WorkflowError("Compiler archive exceeds the size limit.")
    digest = hashlib.sha256()
    with archive.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if not re.fullmatch(r"[0-9a-f]{64}", expected_hash) or digest.hexdigest() != expected_hash:
        raise WorkflowError("Compiler archive SHA-256 does not match the committed pin; nothing was installed.")
    prefix = f"typst-{target}"
    binary = "typst.exe" if "windows" in target else "typst"
    required = {f"{prefix}/{name}": name for name in (binary, "LICENSE", "NOTICE")}
    allowed = set(required) | {prefix, f"{prefix}/README.md"}
    seen = set()
    total = 0

    def check(name, size, is_directory, is_regular):
        nonlocal total
        name = name.rstrip("/")
        if name in seen or name not in allowed or len(seen) >= 16:
            raise WorkflowError("Compiler archive has a duplicate or unexpected member.")
        seen.add(name)
        if (name == prefix and not is_directory) or (name != prefix and not is_regular):
            raise WorkflowError("Compiler archive contains a link or non-regular member.")
        limit = MAX_ARCHIVE if name == f"{prefix}/{binary}" else 4 * 1024 * 1024
        total += size
        if size < 0 or size > limit or total > MAX_UNPACKED:
            raise WorkflowError("Compiler archive member exceeds the size limit.")
        return name

    def copy_member(name, source, size):
        if name not in required:
            return
        with (destination / required[name]).open("xb") as output:
            remaining = size
            while remaining:
                chunk = source.read(min(1024 * 1024, remaining))
                if not chunk:
                    raise WorkflowError("Compiler archive member is truncated.")
                output.write(chunk)
                remaining -= len(chunk)

    try:
        if archive.name.endswith(".zip"):
            with zipfile.ZipFile(archive) as bundle:
                for member in bundle.infolist():
                    if member.orig_filename != member.filename:
                        raise WorkflowError("Compiler archive contains a malformed member name.")
                    if member.external_attr & 0x400:
                        raise WorkflowError("Compiler archive contains a Windows reparse/link member.")
                    mode = member.external_attr >> 16
                    kind = stat.S_IFMT(mode)
                    regular = not member.is_dir() and kind in (0, stat.S_IFREG)
                    directory = member.is_dir() and kind in (0, stat.S_IFDIR)
                    name = check(member.filename, member.file_size, directory, regular)
                    if name in required:
                        with bundle.open(member) as source:
                            copy_member(name, source, member.file_size)
        else:
            with tarfile.open(archive, mode="r:xz") as bundle:
                for member in bundle:
                    regular = member.type in (tarfile.REGTYPE, tarfile.AREGTYPE) and not member.sparse
                    name = check(member.name, member.size, member.isdir(), regular)
                    if name in required:
                        source = bundle.extractfile(member)
                        if source is None:
                            raise WorkflowError("Compiler archive member is unreadable.")
                        with source:
                            copy_member(name, source, member.size)
    except (tarfile.TarError, zipfile.BadZipFile, EOFError, ValueError, RuntimeError, NotImplementedError, lzma.LZMAError, zlib.error) as exc:
        raise WorkflowError("Compiler archive is malformed; nothing was installed.") from exc
    if not set(required).issubset(seen):
        raise WorkflowError("Compiler archive is missing its binary, LICENSE or NOTICE.")
    installed = destination / binary
    installed.chmod(0o755)
    return installed


def install_compiler():
    target = platform_target()
    manifest = read_json(ROOT / "tools" / "typst-release.json")
    if manifest.get("version") != VERSION:
        raise WorkflowError("Compiler manifest version disagrees with the workflow.")
    asset = manifest.get("assets", {}).get(target, {})
    expected_file = f"typst-{target}.{'zip' if 'windows' in target else 'tar.xz'}"
    if asset.get("file") != expected_file:
        raise WorkflowError("Compiler manifest is missing the exact official platform asset.")
    tools = safe_destination(ROOT / ".tools")
    tools.mkdir(exist_ok=True)
    installation = safe_destination(tools / f"typst-{VERSION}")
    with exclusive_lock(tools / ".install-lock"):
        existing = discover_compiler(local_only=True)
        if existing:
            return existing
        with transaction_stage(tools, ".install-") as stage:
            archive = stage / expected_file
            url = f"https://github.com/typst/typst/releases/download/v{VERSION}/{expected_file}"
            download_archive(url, archive)
            fresh = stage / "new"
            fresh.mkdir()
            executable = unpack_archive(archive, fresh, target, asset.get("sha256", ""))
            if not exact_compiler(executable):
                raise WorkflowError("Verified compiler cannot run as the required version on this machine; existing installation is unchanged.")
            backup = stage / "old"
            safe_destination(installation)
            had_old = installation.exists()
            if had_old:
                installation.rename(backup)
            try:
                fresh.rename(installation)
            except OSError:
                if had_old:
                    backup.rename(installation)
                raise
    return local_binary()


def compiler_required(explicit=None):
    compiler = discover_compiler(explicit)
    if compiler is None:
        raise WorkflowError(f"Typst {VERSION} was not found. Run python3 tools/resume.py setup, or provide --typst PATH for an offline compiler.")
    return compiler


def initialize_workspace():
    workspace = safe_destination(ROOT / "workspace")
    if workspace.exists():
        raise WorkflowError("workspace already exists; init refuses to overwrite or merge edited files. Move it aside before initializing again.")
    with tempfile.TemporaryDirectory(prefix=".init-", dir=ROOT) as temporary:
        stage = Path(temporary) / "workspace"
        stage.mkdir()
        shutil.copyfile(ROOT / "examples" / "profile.json", stage / "profile.json")
        shutil.copytree(ROOT / "examples" / "applications", stage / "applications")
        shutil.copyfile(ROOT / "themes" / "classic.json", stage / "theme.json")
        safe_destination(workspace)
        if workspace.exists():
            raise WorkflowError("workspace appeared during initialization; no files were overwritten.")
        stage.rename(workspace)
    print(f"Initialized fictional editable workspace: {workspace}")


def compile_document(compiler, source, output, inputs, fonts):
    command = [str(compiler), "compile", "--root", str(ROOT)]
    for name, path in inputs.items():
        command.extend(["--input", f"{name}=/{path.relative_to(ROOT).as_posix()}"])
    for font in fonts:
        command.extend(["--font-path", str(font)])
    command.extend([str(source), str(output)])
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        # Source excerpts may contain private JSON. Keep native error/help messages only.
        lines = [line.strip() for line in result.stderr.splitlines() if line.strip().startswith(("error:", "help:"))]
        detail = "\n".join(lines[:6])[:1600] or f"Compiler exited with status {result.returncode}."
        raise WorkflowError(f"Could not build {source.name}; previous outputs are unchanged.\n{detail}")


def publish_outputs(stage, pending, stale):
    """Rollback handled rename failures; this is not a crash-atomic transaction."""
    backup = stage / "backup"
    backup.mkdir()
    moved_old = []
    moved_new = []
    try:
        for destination in dict.fromkeys([*pending.keys(), *stale]):
            safe_destination(destination)
            if destination.exists():
                if not destination.is_file():
                    raise WorkflowError(f"Expected a regular output file: {destination}")
                old = backup / destination.name
                destination.replace(old)
                moved_old.append((old, destination))
        for destination, staged in pending.items():
            safe_destination(destination)
            staged.replace(destination)
            moved_new.append(destination)
    except (OSError, WorkflowError, KeyboardInterrupt) as exc:
        rollback_errors = []
        for destination in reversed(moved_new):
            try:
                destination.unlink()
            except OSError as failure:
                rollback_errors.append(str(failure))
        for old, destination in reversed(moved_old):
            try:
                old.replace(destination)
            except OSError as failure:
                rollback_errors.append(str(failure))
        if rollback_errors:
            # Keep recovery files outside the temporary context before reporting failure.
            recovery = safe_destination(ROOT / "build" / f"recovery-{stage.name}")
            backup.rename(recovery)
            raise WorkflowError(f"Publication and rollback failed. Preserved backups at {recovery}; recover files before rebuilding.") from exc
        raise WorkflowError("Publication failed; previous requested outputs were restored.") from exc


def build_documents(args):
    inputs = {name: input_path(getattr(args, name)) for name in ("profile", "application", "theme")}
    identifier = application_id(inputs["application"])
    fonts = [input_path(path, directory=True) for path in args.font_path]
    compiler = compiler_required(args.typst)
    build = safe_destination(ROOT / "build")
    build.mkdir(exist_ok=True)
    surfaces = ("cv", "letter") if args.document == "both" else (args.document,)
    with exclusive_lock(build / ".publish-lock"):
        with transaction_stage(build, ".stage-") as stage:
            pending = {}
            stale = []
            for surface in surfaces:
                folder, stem = ("resumes", f"resume-{identifier}") if surface == "cv" else ("cover-letters", f"cover-letter-{identifier}")
                destination_dir = safe_destination(build / folder)
                destination_dir.mkdir(exist_ok=True)
                pdf = stage / f"{stem}.pdf"
                compile_document(compiler, ROOT / f"{surface}.typ", pdf, inputs, fonts)
                if not pdf.is_file():
                    raise WorkflowError("Compiler did not produce the requested PDF; previous outputs are unchanged.")
                pending[safe_destination(destination_dir / pdf.name)] = pdf
                page_pattern = re.compile(re.escape(stem) + r"-page-[0-9]+\.png", re.ASCII)
                stale.extend(path for path in destination_dir.iterdir() if page_pattern.fullmatch(path.name))
                if args.preview:
                    compile_document(compiler, ROOT / f"{surface}.typ", stage / f"{stem}-page-{{p}}.png", inputs, fonts)
                    pages = sorted((path for path in stage.iterdir() if page_pattern.fullmatch(path.name)), key=lambda path: int(path.stem.rsplit("-", 1)[1]))
                    if not pages:
                        raise WorkflowError("Compiler did not produce requested PNG previews; previous outputs are unchanged.")
                    for page in pages:
                        pending[safe_destination(destination_dir / page.name)] = page
            publish_outputs(stage, pending, stale)
            for path in pending:
                print(path)


def parser():
    result = argparse.ArgumentParser(description="Install Typst, initialize a private JSON workspace, and build selected native documents. Paths are relative to the repository root.")
    commands = result.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("setup", help="Find exact Typst 0.15.1 or install its verified official release locally.")
    setup.add_argument("--typst", metavar="PATH", help="Use an explicit trusted executable (also works offline).")
    setup.add_argument("--local", action="store_true", help="Prefer/install project-local Typst rather than PATH (an explicit --typst still takes priority).")
    doctor = commands.add_parser("doctor", help="Report platform and exact compiler availability without downloading.")
    doctor.add_argument("--typst", metavar="PATH")
    commands.add_parser("init", help="Copy fictional examples into workspace; refuse any existing workspace.")
    build = commands.add_parser("build", help="Stage selected documents and publish only after every requested compile succeeds.")
    build.add_argument("--document", choices=("cv", "letter", "both"), default="cv")
    build.add_argument("--preview", action="store_true", help="Export every page as PNG beside its PDF.")
    build.add_argument("--profile", default="workspace/profile.json")
    build.add_argument("--application", default="workspace/applications/general.json")
    build.add_argument("--theme", default="workspace/theme.json")
    build.add_argument("--font-path", action="append", default=[], metavar="PATH", help="Additional project-contained font directory; repeatable.")
    build.add_argument("--typst", metavar="PATH", help="Explicit trusted Typst 0.15.1 executable.")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "setup":
            compiler = discover_compiler(args.typst, local_only=args.local)
            print(compiler or install_compiler())
        elif args.command == "doctor":
            print(f"Python {platform.python_version()} | {platform.system()} {platform.machine()} | required Typst {VERSION}")
            try:
                print(f"Official install target: {platform_target()}")
            except WorkflowError as exc:
                print(str(exc))
            print(f"Compiler: {compiler_required(args.typst)}")
        elif args.command == "init":
            initialize_workspace()
        else:
            build_documents(args)
        return 0
    except (WorkflowError, OSError, urllib.error.URLError, subprocess.SubprocessError) as exc:
        print(f"resume-kit: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("resume-kit: interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
