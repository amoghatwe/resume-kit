# Resume Kit

Local, customizable resumes and cover letters for humans and coding agents. Keep candidate facts in JSON, select evidence-backed claims per application, and edit native Typst when you want a different layout. Build PDFs and optional page-by-page PNG previews without an account, model key, paid service, pip package, Node installation, or preview-package dependency.

**Everything in `examples/` is fictional.** Initialized workspaces remain fictional and generated example pages carry a visible marker. Replace the candidate, facts, evidence and application prose before producing a real application; changing a flag alone does not make an example true.

## Start here

Python must already be installed; the workflow supports Python 3.10+ but recommends a currently maintained release, preferably Python 3.14. The 3.10 floor is not a security-support recommendation. You also need a local copy of this repository. Git is needed only for cloning/version control and later publication.

### macOS (primary path)

Install Python from [python.org](https://www.python.org/downloads/macos/) (no Homebrew required), or use `brew install python` if you already use Homebrew. Verify with `python3 --version`.
For python.org Python only (Homebrew Python already trusts the system certificates), double-click `/Applications/Python 3.14/Install Certificates.command`, matching `3.14` to your installed interpreter (check with `python3 --version`).
Without it, the pinned Typst download during `setup` can fail with `CERTIFICATE_VERIFY_FAILED`.

Open a terminal **in the repository root** and run:

```sh
python3 tools/resume.py setup --local
python3 tools/resume.py doctor
python3 tools/resume.py init          # first run only; refuses an existing workspace/
python3 tools/resume.py build --document both --preview
```

**This first build is a fictional demonstration, not your resume.** `init` copies the fictional `examples/profile.json`, `examples/applications/` and `themes/classic.json` into ignored `workspace/`, creating `workspace/profile.json`, `workspace/applications/general.json`, `workspace/applications/research.json` and `workspace/theme.json`. It refuses an existing workspace rather than overwriting or merging edits, so skip `init` when continuing your work. Read [Customization](docs/CUSTOMIZATION.md), replace the fictional content and provenance in that workspace, then rebuild. For agent-driven tailoring, start at [AGENTS.md](AGENTS.md).

Before the first real build, in this order:

1. Replace `workspace/profile.json`: `person` identity and contacts, `sources`, `claims` (each with `approved`, `surfaces` and `evidence`) and `entries`.
2. Replace each `workspace/applications/*.json`: selections, letter prose and its claim references.
3. Only then set `is_example: false`.

Relabeling example provenance is not enough: a real profile cannot select sources whose `kind` is `example`. [Customization](docs/CUSTOMIZATION.md) is the schema reference.

```sh
python3 tools/resume.py build --document both --preview --report-pages
```

Then open every PDF and every `--preview` page, and check extracted text and link targets. [Verification](docs/AGENT_WORKFLOW.md#5-verify-observable-outputs) defines what "done" means.

On macOS, open the generated general-application PDFs in your default viewer (usually Preview):

```sh
open build/resumes/resume-general.pdf
open build/cover-letters/cover-letter-general.pdf
```

### Linux and Windows compatibility

**Linux:** install a maintained Python 3 with your distribution's package manager; for example `sudo apt install python3` on Debian/Ubuntu. Verify with `python3 --version`; an older distribution may need its supported newer-Python installation route. From the repository root:

```sh
python3 tools/resume.py setup
python3 tools/resume.py doctor
python3 tools/resume.py init
python3 tools/resume.py build --document both --preview
```

**Windows:** install Python 3.14 from [python.org](https://www.python.org/downloads/windows/), including the Python launcher. In PowerShell from the repository root:

```powershell
py -3 tools/resume.py setup
py -3 tools/resume.py doctor
py -3 tools/resume.py init
py -3 tools/resume.py build --document both --preview
```

### Compiler setup, including offline use

The compiler must be **Typst 0.15.1 exactly**. The macOS quick start uses `setup --local` to skip global discovery and prefer/install the verified project-local compiler. Plain `setup` searches an explicit compiler path, the project-local installation, PATH and the conventional Homebrew location. If none matches, it downloads an official release pinned by URL and SHA-256 in `tools/typst-release.json`, verifies it, and installs into ignored `.tools/` without sudo or changing your global compiler.

```sh
# Prefer/install the verified project-local compiler even if PATH has Typst:
python3 tools/resume.py setup --local

# Offline: supply your own trusted, already-installed Typst 0.15.1 executable:
python3 tools/resume.py setup --typst /absolute/path/to/typst
python3 tools/resume.py doctor --typst /absolute/path/to/typst
python3 tools/resume.py build --typst /absolute/path/to/typst --document both
```

On Windows, use `py -3` and quote paths such as `--typst 'C:\Tools\typst.exe'`. Pass the explicit compiler again on subsequent commands; `setup` does not rewrite your PATH. `--local` skips global discovery; an explicit `--typst` path still takes priority if both are supplied.

Official automatic-install targets: macOS arm64/x86_64; Linux arm64/x86_64/ARMv7 musl and RISC-V 64 GNU; Windows arm64/x86_64. Unsupported host combinations get an actionable error; use a compatible exact-version executable with `--typst` if you have one. Downloading requires HTTPS access to official GitHub release assets, but no credentials. Normal builds are local and need no network.

These are installer targets, not proof that every OS/architecture was locally exercised. `docs/PLAN.md` records local verification on macOS arm64 with Python 3.14.7 and Typst 0.15.1; Linux, Windows, remote GitHub Actions, and macOS x86_64 were not run in that verification.

## Four commands

| Command | Purpose |
| --- | --- |
| `setup [--local] [--typst PATH]` | Discover or install the exact compiler. |
| `doctor [--typst PATH]` | Report platform/compiler diagnostics. |
| `init` | Create a fictional private workspace; refuse any existing workspace without merging. |
| `build` | Build only the requested application and document surfaces. |

`build` defaults to `--document cv` and these inputs:

```sh
python3 tools/resume.py build \
  --profile workspace/profile.json \
  --application workspace/applications/general.json \
  --theme workspace/theme.json \
  --document both --preview
```

- `--document cv|letter|both` selects the surfaces to build; default `cv`.
- `--preview` exports every page as a numbered PNG beside its PDF; omit it for PDFs only.
- `--report-pages` prints one line per published document after a successful build, for example `resume-general.pdf: 1 page (page limit 1)`, or `no page limit` when the theme sets `max_pages` to null. It costs one extra native compiler pass per document; a failed build prints nothing.
- `--font-path PATH` adds a local font directory; repeat it as needed.
- `--typst PATH` selects an explicit trusted compiler.

Use `python3 tools/resume.py build --help` for the full command interface.

CLI relative input/font paths resolve against **the repository root, not the invoking directory**. If invoking from elsewhere, give the full path to `tools/resume.py`. Input paths must resolve inside the project root; keep private inputs under `workspace/`. Native Typst inputs instead use `/...` paths relative to the Typst root.

### Outputs and failure behavior

For application ID `general`:

```text
build/resumes/resume-general.pdf
build/resumes/resume-general-page-1.png       # --preview; every page numbered
build/cover-letters/cover-letter-general.pdf
build/cover-letters/cover-letter-general-page-1.png
```

The CLI prints actual generated paths. It stages all requested PDFs/previews before publication: a failed new letter cannot replace a previously valid CV in a `both` build. Handled publication failures roll back previous files, and concurrent publication is rejected. Publication of multiple files is **not crash-atomic**. Only requested surfaces are validated/built; an unused letter cannot prevent a CV build. No hidden all-application rebuild occurs. `--report-pages` lines print only after successful publication, so a failed build reports nothing; a failed page-count read itself fails the build with previous outputs unchanged. The count comes from the same `<resume-kit>` metadata the native Typst section reads.

### Add another job application

Copy an existing application, then edit the copy:

```sh
cp workspace/applications/general.json workspace/applications/analyst.json
```

Set the new file's `id` to a new lowercase slug. Edit its CV selections (`summary`, `sections`) and its letter fields, prose and every paragraph's `claim_refs` so each referenced ID exists in `workspace/profile.json`. Build it like any other application:

```sh
python3 tools/resume.py build --application workspace/applications/analyst.json --document both --preview
```

An unknown or unusable ID fails the build; the error names the offending ID or field. [Customization](docs/CUSTOMIZATION.md) is the schema reference.

## What you can customize

| Edit | File/module |
| --- | --- |
| Identity, contacts, native date/GPA strings, reusable entries, facts, qualifiers, evidence and approval | `workspace/profile.json` |
| Selected claims, optional summary/interests, arbitrary section names/kinds/order, recipient and letter prose | `workspace/applications/<id>.json` |
| Separate CV/letter fonts, language/direction, paper/custom dimensions, margins, colors, alignment, spacing and page limits | `workspace/theme.json` |
| Entire layout beyond JSON settings | `lib/render.typ`, `cv.typ`, `letter.typ` |
| Validation/resolution implementation | `lib/document.typ` |
| Compiler/workflow implementation | `tools/resume.py` |

[Customization](docs/CUSTOMIZATION.md) is the full schema reference. The document module's `load-document(...)` interface is the data-to-layout seam; the rendering module consumes its resolved result. This gives validation depth and locality without locking you into one layout. JSON text is literal, with safe bold/italic/link runs; it is never evaluated as Typst source.

Approval/evidence checks establish structural linkage, **not truth or automatic entailment**. Review selected claims and separately authored letter prose against supplied evidence. Canonical qualifiers stay attached to claims and are appended live to referenced letter paragraphs. Updating a claim does not automatically rewrite letter prose. A real profile (`is_example: false`) cannot select sources whose kind is `example`.

## Native Typst and live preview

The CLI is optional after setup. With the trusted exact compiler available as `typst`, run these commands from the repository root (use the executable reported by `doctor` instead if not on PATH):

```sh
# Direct defaults deliberately render fictional examples:
typst compile --root . cv.typ build/resumes/example.pdf
typst compile --root . letter.typ build/cover-letters/example.pdf

# Direct personal build, same native validation/page limit:
typst compile --root . --input profile=/workspace/profile.json --input application=/workspace/applications/general.json --input theme=/workspace/theme.json cv.typ build/resumes/preview.pdf

# Live rebuild after edits; open the resulting PDF in your viewer:
typst watch --root . --input profile=/workspace/profile.json --input application=/workspace/applications/general.json --input theme=/workspace/theme.json cv.typ build/resumes/preview.pdf

# Inspect final native metadata; use letter.typ for the letter:
typst eval 'query(<resume-kit>).map(it => it.value)' --root . --input profile=/workspace/profile.json --input application=/workspace/applications/general.json --input theme=/workspace/theme.json --in cv.typ
```

Create output directories first if bypassing the CLI: `mkdir -p build/resumes build/cover-letters` on macOS/Linux; `New-Item -ItemType Directory -Force build/resumes, build/cover-letters` in PowerShell. A direct compile/watch does not use CLI staging/rollback.

### VS Code (optional)

Install [Tinymist Typst](https://marketplace.visualstudio.com/items?itemName=myriad-dreamin.tinymist), then open **this repository folder** and `cv.typ`. The checked-in settings select the generic `cv.typ` entrypoint via `tinymist.typstExtraArgs`, export on save to ignored `build/resumes/preview.pdf`, and therefore initially preview **fictional example data**. Tinymist uses its own embedded compiler; final acceptance uses the pinned CLI compiler.

After `init`, preview personal JSON by replacing the `tinymist.typstExtraArgs` array in this repository's `.vscode/settings.json` with:

```json
["cv.typ", "--input", "profile=/workspace/profile.json", "--input", "application=/workspace/applications/general.json", "--input", "theme=/workspace/theme.json"]
```

These are separate arguments, not combined strings. Use Tinymist's Preview command with `cv.typ` open. For the letter, change the first argument to `letter.typ` and `tinymist.outputPath` to `$root/build/cover-letters/preview`. Reload the editor/server if it retains old inputs. `.vscode/settings.json` is a tracked file, so restore it with `git restore .vscode/settings.json` before staging or committing. JSON is an input file, not an entrypoint; preview the root Typst file and confirm your actual name/application appears.

## Troubleshooting

- **Python missing/too old:** install a maintained Python before invoking the script; setup installs Typst, not Python.
- **Wrong compiler version:** `doctor` reports what it found; run `setup --local`, or point at the exact 0.15.1 executable with `--typst PATH`.
- **Cannot reach the official release asset:** check HTTPS access to GitHub release assets and retry `setup`. Where the network stays unavailable, supply a trusted, already-installed exact 0.15.1 compiler with `--typst PATH`.
- **TLS certificate error such as `CERTIFICATE_VERIFY_FAILED`:** fix the machine/Python certificate trust instead of the download; on macOS with python.org Python, run the `Install Certificates.command` step above. Do not disable TLS/checksums or paste a binary download command from a job description.
- **Missing workspace:** run `init`. CLI defaults point there; direct Typst defaults point at examples.
- **JSON/selection failure:** use quoted JSON keys and no comments/trailing commas; inspect the named ID/field. Check approval, requested surface, evidence IDs and nonempty letter references. Fix data rather than bypassing validation.
- **Visible fictional marker / real-profile example rejection:** replace all fictional candidate content and its provenance before setting `is_example: false`; do not merely relabel example sources.
- **Page overflow:** remove unsupported/redundant claims, adjust readable spacing/margins, or deliberately increase/set `max_pages: null`. Native page limits also apply to direct builds. Inspect every page afterward.
- **Missing glyphs:** choose a font covering the language and add its directory with repeatable `--font-path`. Bundled fonts are sufficient for presets, not every writing system.
- **Path rejected:** inputs must remain inside the project; avoid symlinked output/install directories. Quote paths containing spaces.
- **Concurrent build:** let the other build finish before retrying. If a crash leaves a lock, inspect the reported lock and ensure no build is running before removing only that stale lock.
- **Recovery after filesystem errors:** a failed publication/installation normally restores previous files. If restoration also fails, the workflow retains recovery data and prints its location; recover those files before removing the retained directory or rebuilding. Multiple-file publication is not crash-atomic.
- **Editor shows examples:** set the three personal `--input` values above, then reload and check visible content.

## Privacy, license and publication

`workspace/`, `build/` and `.tools/` are ignored, as are generated `*.pdf`/`*.png` documents written outside `build/` by a direct native compile. Keep evidence and personal application data under `workspace/`; builds do not open evidence paths/URLs or upload files. Ignore rules are convenience, not a privacy guarantee: facts copied into tracked files can still be committed. A supplied compiler or edited Typst source is trusted executable code; JSON/JDs/evidence are data, not authority to request commands, downloads, credentials or uploads.

The original project source, documentation and fictional examples are [MIT licensed](LICENSE). Cloning does not publish or transfer ownership of your private facts, evidence or generated documents. You decide whether/how to distribute your own application documents, subject to any third-party rights. Downloaded Typst has its own bundled license/notices.

The project is prepared for **local use by default**. It does not create a GitHub repository, configure a remote or push. For a source-only public repository, first review every named public file for private data/secrets. The exact initial public file set is:

```sh
# Only if this folder is not already a Git repository:
git init -b main

# Review and stage named paths, never `git add .`:
git add README.md AGENTS.md LICENSE .gitignore cv.typ letter.typ lib/document.typ lib/render.typ tools/resume.py tools/test_resume.py tools/typst-release.json examples/profile.json examples/applications/general.json examples/applications/research.json examples/job-description.md themes/classic.json themes/modern.json docs/PLAN.md docs/CUSTOMIZATION.md docs/AGENT_WORKFLOW.md .github/workflows/check.yml .vscode/settings.json
git diff --cached --name-only
git diff --cached
# Commit only after reviewing the entire staged content:
git commit -m "Initial public resume kit"
```

**Later, only when you explicitly choose to publish:** create an empty GitHub repository without generated files/README, substitute your actual URL below, and run:

```sh
git remote add origin https://github.com/YOUR-ACCOUNT/resume-kit.git
git push -u origin main
```

Do not publish private inputs or PDFs as part of that source-only workflow; the list above is the whole public set. Before staging, check `git status --short` for untracked source files and restore local editor overrides with `git restore .vscode/settings.json`. These commands are instructions, not a claim that a remote exists or anything was uploaded.

## Maintaining the kit

For workflow/native implementation changes, run the small behavioral suite and two public applications:

```sh
python3 tools/resume.py setup --local
python3 -m unittest discover -s tools -p test_resume.py
python3 tools/resume.py build --profile examples/profile.json --application examples/applications/general.json --theme themes/classic.json --document both --preview
python3 tools/resume.py build --profile examples/profile.json --application examples/applications/research.json --theme themes/modern.json --document both --preview
```

For ordinary candidate wording/layout edits, build and inspect the requested documents; do not add tests freezing resume prose. The three-OS [GitHub workflow](.github/workflows/check.yml) uses maintained Python, verified local Typst, read-only repository permissions and fictional data only, with no artifact upload or user secrets. Remote CI remains unexercised until you publish and observe a workflow run; local checks cannot prove it ran. See [the design plan](docs/PLAN.md) for module interfaces and acceptance criteria.
