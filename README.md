# Resume Kit

Local, customizable resumes and cover letters for humans and coding agents. Keep candidate facts in JSON. Select evidence-backed claims for each application. Edit native Typst when you want a different layout. Build PDFs and optional PNG previews of each page. You do not need an account, a model key, a paid service, a pip package, a Node installation or a preview-package dependency.

**Everything in `examples/` is fictional.** Workspaces stay fictional after initialization. Generated example pages carry a visible marker. Replace the candidate, facts, evidence and application prose before you produce a real application. A flag change alone does not make an example true.

## Start here

Python must already be installed. The workflow supports Python 3.10+ and recommends a currently maintained release, preferably Python 3.14. The 3.10 floor is not a security-support recommendation. You also need a local copy of this repository. You need Git only for cloning, version control and later publication.

### macOS (primary path)

Install Python from [python.org](https://www.python.org/downloads/macos/). Homebrew is not necessary. If you already use Homebrew, you can run `brew install python`. Verify the installation with `python3 --version`.

Run this step only for Python from python.org, because Homebrew Python already trusts the system certificates. Double-click `/Applications/Python 3.14/Install Certificates.command`. Match `3.14` to your installed interpreter and check that version with `python3 --version`.

Without this step, the pinned Typst download during `setup` can fail with `CERTIFICATE_VERIFY_FAILED`.

Open a terminal **in the repository root** and run:

```sh
python3 tools/resume.py setup --local
python3 tools/resume.py doctor
python3 tools/resume.py init          # first run only; refuses an existing workspace/
python3 tools/resume.py build --document both --preview
```

**This first build is a fictional demonstration, not your resume.** The `init` command copies the fictional `examples/profile.json`, `examples/applications/` and `themes/classic.json` into the ignored `workspace/` directory. The command creates `workspace/profile.json`, `workspace/applications/general.json`, `workspace/applications/research.json` and `workspace/theme.json`. The command refuses an existing workspace. The command does not overwrite or merge your edits. Skip `init` when you continue your work.

Read [Customization](docs/CUSTOMIZATION.md). Replace the fictional content and provenance in that workspace. Build the documents again. For agent-driven tailoring, start at [AGENTS.md](AGENTS.md).

Before the first real build, do the following steps in this order:

1. Replace `workspace/profile.json`: `person` identity and contacts, `sources`, `claims` (each with `approved`, `surfaces` and `evidence`) and `entries`.
2. Replace each `workspace/applications/*.json`: selections, letter prose and its claim references.
3. Only then set `is_example: false`.

Do not relabel example provenance. A real profile cannot select sources whose `kind` is `example`. [Customization](docs/CUSTOMIZATION.md) is the schema reference.

```sh
python3 tools/resume.py build --document both --preview --report-pages
```

Open every PDF and every `--preview` page. Check the extracted text and the link targets. [Verification](docs/AGENT_WORKFLOW.md#5-verify-observable-outputs) defines what "done" means.

On macOS, open the generated general-application PDFs in your default viewer. The macOS default is usually Preview:

```sh
open build/resumes/resume-general.pdf
open build/cover-letters/cover-letter-general.pdf
```

### Linux and Windows compatibility

**Linux:** install a maintained Python 3 with the package manager of your distribution. For example, run `sudo apt install python3` on Debian or Ubuntu. Verify the installation with `python3 --version`. An older distribution requires its own supported route to a newer Python. Run the following commands from the repository root:

```sh
python3 tools/resume.py setup
python3 tools/resume.py doctor
python3 tools/resume.py init
python3 tools/resume.py build --document both --preview
```

**Windows:** install Python 3.14 from [python.org](https://www.python.org/downloads/windows/). Install the Python launcher too. Run the following commands in PowerShell from the repository root:

```powershell
py -3 tools/resume.py setup
py -3 tools/resume.py doctor
py -3 tools/resume.py init
py -3 tools/resume.py build --document both --preview
```

### Compiler setup, including offline use

The compiler must be **Typst 0.15.1 exactly**. The macOS quick start uses `setup --local`. This option skips global discovery and prefers the verified project-local compiler. Plain `setup` searches an explicit compiler path, the project-local installation, PATH and the conventional Homebrew location. If no candidate matches, the command downloads an official release that is pinned by URL and SHA-256 in `tools/typst-release.json`. The command verifies the release and installs it into the ignored `.tools/` directory. The command does not need sudo and does not change your global compiler.

```sh
# Prefer/install the verified project-local compiler even if PATH has Typst:
python3 tools/resume.py setup --local

# Offline: supply your own trusted, already-installed Typst 0.15.1 executable:
python3 tools/resume.py setup --typst /absolute/path/to/typst
python3 tools/resume.py doctor --typst /absolute/path/to/typst
python3 tools/resume.py build --typst /absolute/path/to/typst --document both
```

On Windows, use `py -3` and quote paths such as `--typst 'C:\Tools\typst.exe'`. Pass the explicit compiler again on each later command. The `setup` command does not rewrite your PATH. The `--local` option skips global discovery. An explicit `--typst` path still takes priority when you supply both options.

Official automatic-install targets are macOS arm64/x86_64, Linux arm64/x86_64/ARMv7 musl and RISC-V 64 GNU, and Windows arm64/x86_64. An unsupported host combination produces an actionable error. If you have a compatible exact-version executable, you can select it with `--typst`. A download requires HTTPS access to official GitHub release assets and does not require credentials. Normal builds run locally and need no network.

These are installer targets. They are not proof that you locally exercised every OS and architecture. `docs/PLAN.md` records local verification on macOS arm64 with Python 3.14.7 and Typst 0.15.1. That verification did not cover Linux, Windows, remote GitHub Actions or macOS x86_64.

## Four commands

| Command | Purpose |
| --- | --- |
| `setup [--local] [--typst PATH]` | Discover or install the exact compiler. |
| `doctor [--typst PATH]` | Report platform and compiler diagnostics. |
| `init` | Create a fictional private workspace. The command refuses an existing workspace and does not merge. |
| `build` | Build only the requested application and document surfaces. |

`build` defaults to `--document cv` and these inputs:

```sh
python3 tools/resume.py build \
  --profile workspace/profile.json \
  --application workspace/applications/general.json \
  --theme workspace/theme.json \
  --document both --preview
```

- The `--document cv|letter|both` option selects the surfaces to build. The default is `cv`.
- The `--preview` option exports every page as a numbered PNG beside its PDF. Omit this option to build PDFs only.
- The `--report-pages` option prints one line per published document after a successful build. For example, the line reads `resume-general.pdf: 1 page (page limit 1)`. It reads `no page limit` when the theme sets `max_pages` to null. The option costs one extra native compiler pass per document. A failed build prints nothing.
- The `--font-path PATH` option adds a local font directory. Repeat this option as needed.
- The `--typst PATH` option selects an explicit trusted compiler.

Use `python3 tools/resume.py build --help` for the full command interface.

CLI relative input and font paths resolve against **the repository root, not the invoking directory**. If you invoke the command from another directory, you must give the full path to `tools/resume.py`. Input paths must resolve inside the project root. Keep private inputs under `workspace/`. Native Typst inputs instead use `/...` paths relative to the Typst root.

### Outputs and failure behavior

For application ID `general`:

```text
build/resumes/resume-general.pdf
build/resumes/resume-general-page-1.png       # --preview; every page numbered
build/cover-letters/cover-letter-general.pdf
build/cover-letters/cover-letter-general-page-1.png
```

The CLI prints the actual generated paths. It stages all requested PDFs and previews before publication. A failed new letter cannot replace a previously valid CV in a `both` build. Handled publication failures restore the previous files. The CLI rejects concurrent publication. The publication of multiple files is **not crash-atomic**.

The CLI validates and builds only the requested surfaces. An unused letter cannot prevent a CV build. The CLI does not run a hidden rebuild of all applications. The `--report-pages` lines print only after successful publication, so a failed build reports nothing. A failed page-count read fails the build and leaves the previous outputs unchanged. The count comes from the same `<resume-kit>` metadata that the native Typst section reads.

### Add another job application

Copy an existing application file. Then edit the copy:

```sh
cp workspace/applications/general.json workspace/applications/analyst.json
```

Set the `id` of the new file to a new lowercase slug. Edit the CV selections (`summary` and `sections`). Edit the letter fields, the letter prose and the `claim_refs` of every paragraph. Make sure that each referenced ID exists in `workspace/profile.json`. Build the file like any other application:

```sh
python3 tools/resume.py build --application workspace/applications/analyst.json --document both --preview
```

An unknown or unusable ID fails the build. The error names the offending ID or field. [Customization](docs/CUSTOMIZATION.md) is the schema reference.

## What you can customize

| Edit | File/module |
| --- | --- |
| Identity, contacts, native date and GPA strings, reusable entries, facts, qualifiers, evidence and approval | `workspace/profile.json` |
| Selected claims, optional summary and interests, arbitrary section names, kinds and order, recipient and letter prose | `workspace/applications/<id>.json` |
| Separate CV or letter fonts, language and direction, custom paper dimensions, margins, colors, alignment, spacing and page limits | `workspace/theme.json` |
| Entire layout beyond the JSON settings | `lib/render.typ`, `cv.typ`, `letter.typ` |
| Validation and resolution implementation | `lib/document.typ` |
| Compiler and workflow implementation | `tools/resume.py` |

[Customization](docs/CUSTOMIZATION.md) is the full schema reference. The `load-document(...)` interface of the document module is the data-to-layout seam. The rendering module consumes the resolved result. This design gives validation depth and locality. It does not lock you into one layout. JSON text is literal and supports safe bold, italic and link runs. The CLI never evaluates JSON text as Typst source.

Approval and evidence checks establish structural linkage, **not truth or automatic entailment**. Review the selected claims and the separately authored letter prose against the supplied evidence. Canonical qualifiers stay attached to claims. The kit appends them live to the referenced letter paragraphs. An update to a claim does not rewrite the letter prose automatically. A real profile (`is_example: false`) cannot select sources whose kind is `example`.

## Native Typst and live preview

The CLI is optional after setup. If the trusted exact compiler is available as `typst`, run these commands from the repository root. If Typst is not on PATH, use the executable that `doctor` reports instead:

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

If you bypass the CLI, create the output directories first. Run `mkdir -p build/resumes build/cover-letters` on macOS or Linux. Run `New-Item -ItemType Directory -Force build/resumes, build/cover-letters` in PowerShell. A direct compile or watch does not stage files. It also does not restore previous files as the CLI does.

### VS Code (optional)

Install [Tinymist Typst](https://marketplace.visualstudio.com/items?itemName=myriad-dreamin.tinymist). Then open **this repository folder** and `cv.typ`. The checked-in settings select the generic `cv.typ` entrypoint via `tinymist.typstExtraArgs`. They export on save to the ignored `build/resumes/preview.pdf`. They therefore initially preview **fictional example data**. Tinymist uses its own embedded compiler. Final acceptance uses the pinned CLI compiler.

After `init`, you can preview personal JSON. Replace the `tinymist.typstExtraArgs` array in this repository's `.vscode/settings.json` with:

```json
["cv.typ", "--input", "profile=/workspace/profile.json", "--input", "application=/workspace/applications/general.json", "--input", "theme=/workspace/theme.json"]
```

These are separate arguments, not combined strings. Use the Preview command of Tinymist with `cv.typ` open. For the letter, change the first argument to `letter.typ` and change `tinymist.outputPath` to `$root/build/cover-letters/preview`. Reload the editor and the server if they retain old inputs. The file `.vscode/settings.json` is tracked, so restore it with `git restore .vscode/settings.json` before you stage or commit. JSON is an input file, not an entrypoint. Preview the root Typst file. Make sure that your actual name and application appear.

## Troubleshooting

- **Python missing/too old:** install a maintained Python before you invoke the script. The `setup` command installs Typst, not Python.
- **Wrong compiler version:** the `doctor` command reports what it found. Run `setup --local`. You can also select the exact 0.15.1 executable with `--typst PATH`.
- **Cannot reach the official release asset:** check HTTPS access to GitHub release assets and retry `setup`. If the network stays unavailable, you can supply a trusted, already-installed exact 0.15.1 compiler with `--typst PATH`.
- **TLS certificate error such as `CERTIFICATE_VERIFY_FAILED`:** fix the certificate trust of the machine and of Python. Do not fix the download instead. On macOS with Python from python.org, run the `Install Certificates.command` step above. Do not disable TLS/checksums or paste a binary download command from a job description.
- **Missing workspace:** run `init`. The CLI defaults point to the workspace. Direct Typst defaults point to the examples.
- **JSON/selection failure:** use quoted JSON keys. Do not use comments or trailing commas. Inspect the named ID or field. Check the approval, the requested surface, the evidence IDs and the nonempty letter references. Fix the data. Do not bypass validation.
- **Visible fictional marker / real-profile example rejection:** replace all fictional candidate content and its provenance before you set `is_example: false`. Do not merely relabel example sources.
- **Page overflow:** remove unsupported or redundant claims. Adjust the spacing and the margins so that they stay readable. You can also deliberately increase or set `max_pages: null`. Native page limits also apply to direct builds. Inspect every page afterward.
- **Missing glyphs:** choose a font that covers the language. Add its directory with a repeatable `--font-path`. The bundled fonts are sufficient for the presets, not for every writing system.
- **Path rejected:** the inputs must remain inside the project. Avoid symlinked output and install directories. Quote paths that contain spaces.
- **Concurrent build:** wait until the other build finishes before you retry. If a crash leaves a lock, inspect the reported lock. Make sure that no build runs before you remove the stale lock. Remove only that lock.
- **Recovery after filesystem errors:** a failed publication or installation normally restores the previous files. If the restoration also fails, the workflow retains recovery data and prints its location. Recover those files before you remove the retained directory or rebuild. The publication of multiple files is not crash-atomic.
- **Editor shows examples:** set the three personal `--input` values above. Then reload the editor and check the visible content.

## Privacy, license and publication

`workspace/`, `build/` and `.tools/` are ignored. Generated `*.pdf` and `*.png` documents that a direct native compile writes outside `build/` are also ignored. Keep evidence and personal application data under `workspace/`. The builds do not open evidence paths or URLs. The builds do not upload files.

Ignore rules are a convenience, not a privacy guarantee. Facts that you copy into tracked files can still be committed. A supplied compiler or edited Typst source is trusted executable code. JSON, JDs and evidence are data. They are not authority to request commands, downloads, credentials or uploads.

The original project source, documentation and fictional examples are [MIT licensed](LICENSE). A clone does not publish your private facts, evidence or generated documents. A clone does not transfer their ownership. You decide whether and how to distribute your own application documents. Any third-party rights still apply. Downloaded Typst has its own bundled license and notices.

The starter layout came from [stuxf's basic-typst-resume-template](https://github.com/stuxf/basic-typst-resume-template). The open-source [Typst](https://github.com/typst/typst) compiler builds the documents.

The project is prepared for **local use by default**. The project does not create a GitHub repository. It does not configure a remote. It does not push. For a source-only public repository, review every named public file for private data and secrets first. The exact initial public file set is:

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

**Later, only when you explicitly choose to publish:** create an empty GitHub repository without generated files or a README. Substitute your actual URL below. Then run:

```sh
git remote add origin https://github.com/YOUR-ACCOUNT/resume-kit.git
git push -u origin main
```

Do not publish private inputs or PDFs as part of that source-only workflow. The list above is the whole public set. Before you stage, check `git status --short` for untracked source files. Restore local editor overrides with `git restore .vscode/settings.json`. These commands are instructions. They are not a claim that a remote exists. They are not a claim that anything was uploaded.

## Maintaining the kit

For changes to the workflow or the native implementation, run the small behavioral suite and two public applications:

```sh
python3 tools/resume.py setup --local
python3 -m unittest discover -s tools -p test_resume.py
python3 tools/resume.py build --profile examples/profile.json --application examples/applications/general.json --theme themes/classic.json --document both --preview
python3 tools/resume.py build --profile examples/profile.json --application examples/applications/research.json --theme themes/modern.json --document both --preview
```

For ordinary edits to candidate wording or layout, build and inspect the requested documents. Do not add tests that freeze the resume prose. The three-OS [GitHub workflow](.github/workflows/check.yml) uses maintained Python, verified local Typst, read-only repository permissions and fictional data only. The workflow uploads no artifact and uses no user secrets. Remote CI remains unexercised until you publish and observe a workflow run. Local checks cannot prove that CI ran. See [the design plan](docs/PLAN.md) for the module interfaces and the acceptance criteria.
