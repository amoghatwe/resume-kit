# Customization reference

Use JSON for normal content/theme changes; use editable Typst for layouts beyond those settings. All examples below are **fictional demonstrations**, not applicant facts. Start with `python3 tools/resume.py init`, edit ignored `workspace/`, then build only your chosen application. Setup and platform instructions are in [README](../README.md); evidence-driven tailoring is in [Agent workflow](AGENT_WORKFLOW.md).

## Files, paths and validation

Each profile/application/theme has integer `schema_version: 1`. JSON supports no comments or trailing commas. Keep all inputs inside the repository, normally in `workspace/`; evidence paths/URLs are descriptive strings and are never fetched/opened by a build.

The CLI takes repository-relative filesystem paths (`workspace/profile.json`). Native `sys.inputs` takes Typst-root-relative paths beginning with `/` (`/workspace/profile.json`). The CV and letter entrypoints accept `profile`, `application` and `theme`; direct defaults are `/examples/profile.json`, `/examples/applications/general.json`, `/themes/classic.json`. CLI defaults use workspace files. Validation resolves only the requested surface. It checks selected claims/entries, not whether your evidence actually entails your prose.

The document module exports:

```typst
#import "/lib/document.typ": load-document
#let document = load-document(
  "/workspace/profile.json",
  "/workspace/applications/general.json",
  "/workspace/theme.json",
  surface: "cv",
)
```

Its resolved interface is `{surface, application_id, is_example, person, theme, summary, sections, letter}`. In native Typst that is a dictionary; `theme` contains only the selected surface's settings. Claims become `{id, text, qualifier}`; section items are resolved claims or entries with metadata/claims; letter paragraphs contain text/resolved claims. Inapplicable arrays are empty and an inapplicable letter is `null`. The rendering module consumes that result without reopening JSON or duplicating approval/evidence checks.

## Profile: canonical facts and entries

Top-level fields:

| Field | Shape and meaning |
| --- | --- |
| `schema_version` | Required integer `1`. |
| `is_example` | Required actual boolean. `true` produces a visible fictional marker on every page. |
| `person` | Required identity object: required `name` string; optional `headline` string, default `""`; optional ordered `contacts` array, default `[]`. |
| `sources` | Dictionary keyed by stable evidence IDs. Each selected source requires nonempty `kind` and `description` strings; optional `path`/`url` strings record provenance. Fictional sources use `kind: "example"`. |
| `claims` | Dictionary keyed by globally unique stable claim IDs. See claim shape below. |
| `entries` | Dictionary keyed by reusable entry IDs. See entry shape below. |

Contacts and entry links use `{ "text": "visible label", "url": "https://example.com" }`; `text` is required, `url` optional. Lists preserve order. Use **full** URLs: HTTP(S), `mailto:` or `tel:` only, with no control characters. No scheme is added for you. Example contacts:

```json
[
  {"text": "alex@example.com", "url": "mailto:alex@example.com"},
  {"text": "+1 202 555 0147", "url": "tel:+12025550147"},
  {"text": "Portfolio", "url": "https://example.com/portfolio"},
  {"text": "Example City"}
]
```

A claim:

```json
{
  "text": "Compared three published forecasting baselines for a class project.",
  "qualifier": "Coursework; no claim of production deployment.",
  "approved": true,
  "surfaces": ["cv", "letter"],
  "evidence": ["course-report"]
}
```

- `text` is required RichText (below). `qualifier` is optional RichText, default `""`.
- `approved` is an explicit boolean, not the string `"true"`. Select only approved claims.
- `surfaces` contains `"cv"`, `"letter"`, or both; selected claims must allow the requested surface.
- `evidence` is a nonempty source-ID array. Every selected source must exist and have valid metadata.
- Preserve qualified outcomes, native units/scales, dates, attribution and uncertainty. Approval is a recorded decision, not a compiler-certified truth assessment.
- A profile with `is_example: false` cannot select `kind: "example"` evidence. Replacing/relabeling that kind is not enough: replace all fictional facts and document the actual evidence first.

An entry:

```json
{
  "title": "Example University",
  "subtitle": "BSc, Economics — GPA 7.5/8.0",
  "date": "Sep 2022 – Jun 2025",
  "location": "Example City",
  "links": [{"text": "Course report", "url": "https://example.com/report"}],
  "claims": ["course-method"]
}
```

`title` is required. `subtitle`, `date` and `location` are optional strings, default `""`; `links` and default `claims` are optional arrays, default `[]`. Metadata-only entries are supported. Dates are literal user-owned strings; no date interpretation/current-date insertion occurs. GPA/native academic scales are literal text: there is no automatic 4.0 conversion or guessed grade equivalence. Put candidate assertions requiring evidence into claims; metadata is not independently evidence-checked, so review it too.

### Safe rich text

RichText is either a plain string or an ordered array of runs:

```json
[
  {"text": "Built ", "bold": false},
  {"text": "a reproducible report", "bold": true},
  {"text": " using published data. ", "italic": true},
  {"text": "Read the report", "url": "https://example.com/report"}
]
```

Every run requires `text: string`; optional `bold`/`italic` must be booleans and default to false; optional `url` obeys the same rendered-link rules as contacts. Add spaces inside run text where you want them: runs are concatenated, not separated automatically. This form is supported for claim text, qualifiers and letter paragraph text, not arbitrary metadata fields. Markdown/Typst syntax such as `**bold**`, `#eval(...)` or `$x$` stays literal. Currency, punctuation and Unicode stay text; escape JSON quotation marks/backslashes normally. Rich text is not a route for executing code or embedding arbitrary markup.

## Application: ordered selections and letter prose

| Field | Shape and meaning |
| --- | --- |
| `schema_version` | Required integer `1`. |
| `id` | Required slug, at most 64 characters: `[a-z0-9]+(?:-[a-z0-9]+)*`. It determines output filenames. |
| `summary` | Optional ordered claim-ID array, default `[]`; no automatic summary generation. |
| `sections` | Optional ordered section array, default `[]`. |
| `letter` | Optional object; required when building a letter. |

Section shape is `{ "title": "Your heading", "kind": "entries", "items": [...] }`. `title`, `kind` and `items` are required. All section names and order are your choice; there is no special behavior attached to “Education”, “Skills” or “Interests”. An empty title omits the heading. An empty `items` array omits the entire section, including its heading.

### All four section kinds

| Kind | `items` shape | Rendered form |
| --- | --- | --- |
| `entries` | Ordered `{ "id": "entry-id", "claims": ["claim-id"] }` selections | Entry metadata and selected claim bullets. |
| `bullets` | Ordered claim IDs | Bullet list. |
| `paragraphs` | Ordered claim IDs | Separate body paragraphs. |
| `compact` | Ordered claim IDs | Compact text using theme `compact_separator`. |

For entry selections, **omitting `claims` uses that entry's canonical default claim IDs; explicit `"claims": []` selects no bullets**. Those metadata-only selections still render the entry. Unknown IDs/kinds fail; the renderer does not silently substitute an entry or discard a selected claim. Example:

```json
{
  "schema_version": 1,
  "id": "example-analyst",
  "summary": ["overview"],
  "sections": [
    {"title": "Selected experience", "kind": "entries", "items": [{"id": "role-1"}]},
    {"title": "Education", "kind": "entries", "items": [{"id": "degree-1", "claims": []}]},
    {"title": "Methods", "kind": "bullets", "items": ["methods"]},
    {"title": "Research perspective", "kind": "paragraphs", "items": ["research-note"]},
    {"title": "Languages", "kind": "compact", "items": ["languages"]}
  ]
}
```

This fragment assumes its IDs exist in your profile. To put education first, move that section above experience; to put projects first, move a project section first. To omit the summary, omit `summary` or use `[]`. To add interests, create approved interest claims and a `compact`/other section; to omit interests, do not select that section. Publications, certifications, volunteering, skills and languages use these same four forms—no new implementation branch is needed for each heading.

### Cover letter

`letter` fields:

| Field | Shape and behavior |
| --- | --- |
| `company`, `role` | Required strings. |
| `recipient` | Optional object, omitted by default; optional `name` string (default `""`), optional `address` string array (default `[]`). |
| `date`, `subject` | Optional literal strings, default `""`; absence is not filled with guessed information. |
| `salutation`, `closing` | Required editable strings. Put courtesy text here rather than attaching irrelevant candidate references to a courtesy paragraph. |
| `paragraphs` | Required nonempty ordered array of `{text: RichText, claim_refs: string[]}`. Every paragraph has nonempty canonical candidate claim references valid for `letter`. |

Fictional fragment:

```json
{
  "company": "Example Research Group",
  "role": "Research Analyst",
  "recipient": {"name": "Hiring team", "address": ["Example Research Group"]},
  "subject": "Application for {role}",
  "salutation": "Dear hiring team,",
  "closing": "Kind regards,",
  "paragraphs": [
    {
      "text": "My class-project comparison of published forecasting baselines informs my interest in the {role} position at {company}.",
      "claim_refs": ["course-method"]
    }
  ]
}
```

Only literal `{candidate}`, `{company}` and `{role}` tokens are substituted in paragraph text and literal letter fields; other braces stay literal and no expression is evaluated. Recipient/date/subject may be left out entirely. The candidate's name comes from `person.name`.

Each referenced claim's **current nonempty qualifier is appended after that paragraph**, once per referenced ID in order. Do not maintain qualifier copies in prose. Claim text itself is not automatically copied into or substituted for your independently authored paragraph. A canonical correction therefore requires semantic review of every affected letter paragraph. Claim references cannot prove that the paragraph is entailed, that employer research is true, or that a motivation is authentic. Keep optional employer research notes separate from candidate evidence, and ground motivation manually; no special employer-research field is required by this schema.

## Theme: independent CV and letter settings

A theme is `{ "schema_version": 1, "cv": { ... }, "letter": { ... } }`. **All settings below are explicit in each selected surface**; there is no partial-theme inheritance or merge option. Start by copying `themes/classic.json` or `themes/modern.json`, then change fields in `workspace/theme.json`. An unused surface's settings do not block the requested surface.

| Field | Accepted value / purpose |
| --- | --- |
| `paper` | Typst named paper string, such as `"a4"` or `"us-letter"`, or `{ "width": "210mm", "height": "297mm" }`; dimensions strictly positive. |
| `margins` | Object with `top`, `right`, `bottom`, `left` safe length strings. |
| `font` | Nonempty ordered font-family string array; fallback order is significant. |
| `sizes` | Object with positive `body`, `name`, `heading` safe length strings. |
| `accent` | Exactly `#RRGGBB`, six hexadecimal digits. |
| `alignment` | `"start"`, `"center"` or `"end"`, body alignment. |
| `header_alignment` | `"start"`, `"center"` or `"end"`, name/contact header alignment. |
| `justify` | Boolean, justified body paragraphs. |
| `hyphenate` | Boolean, automatic hyphenation. |
| `heading_rules` | Boolean, section heading rules. |
| `page_numbers` | Boolean, footer page numbers. |
| `language` | Language string passed to native text layout, e.g. `"en"` or `"ar"`. |
| `direction` | `"auto"`, `"ltr"` or `"rtl"`. |
| `spacing` | Object with `leading`, `paragraph`, `list`, `entry`, `section` safe length strings. |
| `rule_width` | Safe length string controlling heading-rule stroke thickness. |
| `contact_separator` | Literal string between ordered contacts. |
| `compact_separator` | Literal string between compact claims. |
| `max_pages` | Positive integer or `null`; native final-layout limit, not a content estimate. |

A complete surface example (use it under `cv` and/or `letter`):

```json
{
  "paper": "a4",
  "margins": {"top": "15mm", "right": "16mm", "bottom": "15mm", "left": "16mm"},
  "font": ["Libertinus Serif"],
  "sizes": {"body": "10pt", "name": "21pt", "heading": "11pt"},
  "accent": "#243746",
  "alignment": "start",
  "header_alignment": "center",
  "justify": false,
  "hyphenate": false,
  "heading_rules": true,
  "page_numbers": false,
  "language": "en",
  "direction": "auto",
  "spacing": {"leading": "0.55em", "paragraph": "0.5em", "list": "0.35em", "entry": "0.7em", "section": "1em"},
  "rule_width": "0.5pt",
  "contact_separator": " | ",
  "compact_separator": " · ",
  "max_pages": 1
}
```

This is an illustrative complete configuration, not a promise that every content selection fits one page. Exact shipped preset values live in the two theme files.

### Lengths, paper and page policy

Safe lengths are nonnegative decimals followed by `pt`, `mm`, `cm`, `in` or `em`, e.g. `"0pt"`, `".5em"`, `"1.25mm"`. Negative values, calculations such as `"10mm + 2pt"`, percentages and executable code are not supported. Font sizes and custom page dimensions must be positive. Named paper support comes from [Typst's page settings](https://typst.app/docs/reference/layout/page/), not a new local paper-size registry.

For US Letter, change `paper` to `"us-letter"`. For custom dimensions, use `{"width": "8in", "height": "10in"}`. Margins/body text must still fit the actual page. For a deliberate two-page CV, use `max_pages: 2`; for unrestricted long-form documents, use `null`. Set `page_numbers: true` where useful. CV and letter limits are independent. The rendering module checks final page count in native Typst, including direct compile/watch, and exposes `{pages, application_id, surface, is_example}` through metadata labeled `<resume-kit>`. Every exported PNG includes its page number—inspect all pages, not only page 1.

### Fonts and multilingual/RTL documents

The presets use bundled proportional fonts (`Libertinus Serif` and `New Computer Modern`) so default builds do not require font downloads. Choose any locally available family via `font`, and supply directories when necessary:

```sh
python3 tools/resume.py build --document both --font-path workspace/fonts --font-path workspace/other-fonts --preview
# Native equivalent font option:
typst compile --root . --font-path workspace/fonts --input profile=/workspace/profile.json --input application=/workspace/applications/general.json --input theme=/workspace/theme.json cv.typ build/resumes/preview.pdf
```

Inspect compiler font discovery with `typst fonts` (add `--font-path` for your directory). For Arabic, for example, set `language: "ar"`, `direction: "rtl"`, and a locally installed Arabic-capable font family. `start`/`end` alignment follows text direction. Native shaping/direction is supported, but bundled baseline fonts do not cover every script. Check mixed-direction dates/contact links, glyph coverage and visual reading order in the actual PDF; no translation or academic-scale conversion is performed.

## Editable Typst escape hatch

`lib/render.typ` exports `render-cv(document)` and `render-letter(document)`. Modify that implementation for a new heading treatment, header, columns, pagination or typography not represented by JSON; modify the thin `cv.typ`/`letter.typ` entrypoints to choose a different renderer or defaults. Keep `load-document(...)` as the resolution seam if you want the evidence/approval guards to remain in force. Native source is trusted executable code; do not paste executable instructions from a JD/evidence document into it.

A new renderer must preserve literal text, full links, qualifier visibility, fictional markers and page-limit/metadata behavior if you want the same completion contract. Arbitrary source changes can bypass those guarantees; review and rebuild them as code changes. Do not add a second JSON parser or a generic plugin layer merely to change layout. ATS-friendly linear flow in the shipped renderer is a design choice, not a guarantee about every employer's parsing system.

For normal tailoring, retain the shared source and change private JSON. Example direct personal commands, from the repository root with the exact trusted compiler:

```sh
typst compile --root . --input profile=/workspace/profile.json --input application=/workspace/applications/general.json --input theme=/workspace/theme.json cv.typ build/resumes/preview.pdf
typst compile --root . --input profile=/workspace/profile.json --input application=/workspace/applications/general.json --input theme=/workspace/theme.json letter.typ build/cover-letters/preview.pdf
```

Create output directories first or use the CLI, which creates/stages them. Verify real output text, links, every-page visual layout and final page count. Passing schema validation alone is not completion.
