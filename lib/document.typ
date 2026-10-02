// The data seam: all selection, provenance and configuration checks live here.
// JSON remains literal text. Neither evidence paths nor data strings are executed.

#let object(value, where) = {
  assert(type(value) == dictionary, message: where + " must be an object")
  value
}
#let array-value(value, where) = {
  assert(type(value) == array, message: where + " must be an array")
  value
}
#let string-value(value, where, nonempty: false) = {
  assert(type(value) == str, message: where + " must be a string")
  if nonempty { assert(value.trim() != "", message: where + " must not be empty") }
  value
}
#let boolean(value, where) = {
  assert(type(value) == bool, message: where + " must be a boolean")
  value
}
#let required(record, key, where) = {
  assert(key in record, message: where + " is missing " + key)
  record.at(key)
}
#let version-one(record, where) = {
  let value = required(record, "schema_version", where)
  assert(type(value) == int and value == 1, message: where + ".schema_version must be integer 1")
}
#let strings(value, where, nonempty: false) = {
  array-value(value, where).map(item => string-value(item, where + " item", nonempty: nonempty))
}
#let safe-url(value, where) = {
  let _ = string-value(value, where, nonempty: true)
  assert(value.match(regex("(?i)^(https?://|mailto:|tel:)\\S+$")) != none
    and value.match(regex("\\p{Cc}")) == none,
    message: where + " must be an HTTP(S), mailto: or tel: URL without whitespace or control characters")
  value
}
#let rich-text(value, where) = {
  if type(value) == str { return value }
  array-value(value, where).map(run => {
    let _ = object(run, where + " run")
    for key in run.keys() {
      assert(key in ("text", "bold", "italic", "url"), message: where + " run has unsupported field " + key)
    }
    let result = (
      text: string-value(required(run, "text", where + " run"), where + " run.text"),
      bold: boolean(run.at("bold", default: false), where + " run.bold"),
      italic: boolean(run.at("italic", default: false), where + " run.italic"),
      url: none,
    )
    if "url" in run { result.url = safe-url(run.url, where + " run.url") }
    result
  })
}
#let contacts(value, where) = {
  array-value(value, where).map(item => {
    let _ = object(item, where + " item")
    (
      text: string-value(required(item, "text", where), where + ".text", nonempty: true),
      url: if "url" in item { safe-url(item.url, where + ".url") } else { none },
    )
  })
}
#let safe-length(value, where, positive: false) = {
  let _ = string-value(value, where)
  let parsed = value.match(regex("^([0-9]+(?:\\.[0-9]+)?|\\.[0-9]+)(pt|mm|cm|in|em)$"))
  assert(parsed != none, message: where + " must be a nonnegative decimal length in pt, mm, cm, in or em")
  let amount = float(parsed.captures.at(0))
  if positive { assert(amount > 0, message: where + " must be positive") }
  amount * ("pt": 1pt, "mm": 1mm, "cm": 1cm, "in": 1in, "em": 1em).at(parsed.captures.at(1))
}
#let length-group(record, keys, where, positive: false) = {
  let _ = object(record, where)
  let result = (:)
  for key in keys {
    result.insert(key, safe-length(required(record, key, where), where + "." + key, positive: positive))
  }
  result
}
#let choice(value, choices, where) = {
  let _ = string-value(value, where)
  assert(value in choices, message: where + " must be one of " + choices.join(", "))
  value
}
#let resolve-theme(raw, surface) = {
  let _ = object(raw, "theme")
  version-one(raw, "theme")
  let settings = object(required(raw, surface, "theme"), "theme." + surface)
  let where = "theme." + surface
  let paper = required(settings, "paper", where)
  if type(paper) == str {
    let _ = string-value(paper, where + ".paper", nonempty: true)
  } else {
    paper = length-group(paper, ("width", "height"), where + ".paper", positive: true)
  }
  let font = strings(required(settings, "font", where), where + ".font", nonempty: true)
  assert(font.len() > 0, message: where + ".font must contain at least one family")
  let accent = string-value(required(settings, "accent", where), where + ".accent")
  assert(accent.match(regex("^#[0-9a-fA-F]{6}$")) != none, message: where + ".accent must be #RRGGBB")
  let alignment = choice(required(settings, "alignment", where), ("start", "center", "end"), where + ".alignment")
  let header-alignment = choice(required(settings, "header_alignment", where), ("start", "center", "end"), where + ".header_alignment")
  let direction = choice(required(settings, "direction", where), ("auto", "ltr", "rtl"), where + ".direction")
  let limit = required(settings, "max_pages", where)
  assert(limit == none or (type(limit) == int and limit > 0), message: where + ".max_pages must be a positive integer or null")
  (
    paper: paper,
    margins: length-group(required(settings, "margins", where), ("top", "right", "bottom", "left"), where + ".margins"),
    font: font,
    sizes: length-group(required(settings, "sizes", where), ("body", "name", "heading"), where + ".sizes", positive: true),
    accent: rgb(accent),
    alignment: (start: start, center: center, end: end).at(alignment),
    header_alignment: (start: start, center: center, end: end).at(header-alignment),
    justify: boolean(required(settings, "justify", where), where + ".justify"),
    hyphenate: boolean(required(settings, "hyphenate", where), where + ".hyphenate"),
    heading_rules: boolean(required(settings, "heading_rules", where), where + ".heading_rules"),
    page_numbers: boolean(required(settings, "page_numbers", where), where + ".page_numbers"),
    language: string-value(required(settings, "language", where), where + ".language", nonempty: true),
    direction: ("auto": auto, "ltr": ltr, "rtl": rtl).at(direction),
    spacing: length-group(required(settings, "spacing", where), ("leading", "paragraph", "list", "entry", "section"), where + ".spacing"),
    rule_width: safe-length(required(settings, "rule_width", where), where + ".rule_width"),
    contact_separator: string-value(required(settings, "contact_separator", where), where + ".contact_separator"),
    compact_separator: string-value(required(settings, "compact_separator", where), where + ".compact_separator"),
    max_pages: limit,
  )
}
#let resolve-claim(id, profile, surface) = {
  let _ = string-value(id, "selected claim ID", nonempty: true)
  assert(id in profile.claims, message: "Unknown selected claim: " + id)
  let where = "claim " + id
  let claim = object(profile.claims.at(id), where)
  assert(boolean(required(claim, "approved", where), where + ".approved"), message: where + " is not approved")
  let surfaces = strings(required(claim, "surfaces", where), where + ".surfaces")
  for allowed in surfaces { let _ = choice(allowed, ("cv", "letter"), where + ".surfaces item") }
  assert(surface in surfaces, message: where + " is not approved for " + surface)
  let evidence = strings(required(claim, "evidence", where), where + ".evidence", nonempty: true)
  assert(evidence.len() > 0, message: where + " requires evidence")
  for source-id in evidence {
    assert(source-id in profile.sources, message: where + " references unknown evidence: " + source-id)
    let source = object(profile.sources.at(source-id), "source " + source-id)
    let kind = string-value(required(source, "kind", "source " + source-id), "source " + source-id + ".kind", nonempty: true)
    let _ = string-value(required(source, "description", "source " + source-id), "source " + source-id + ".description", nonempty: true)
    for field in ("path", "url") {
      if field in source { let _ = string-value(source.at(field), "source " + source-id + "." + field) }
    }
    assert(profile.is_example or kind != "example", message: where + " uses fictional example evidence in a real profile: " + source-id)
  }
  (
    id: id,
    text: rich-text(required(claim, "text", where), where + ".text"),
    qualifier: rich-text(claim.at("qualifier", default: ""), where + ".qualifier"),
  )
}
#let resolve-claims(ids, profile, surface, where) = {
  strings(ids, where, nonempty: true).map(id => resolve-claim(id, profile, surface))
}
#let resolve-entry(selection, profile) = {
  let _ = object(selection, "entry selection")
  let id = string-value(required(selection, "id", "entry selection"), "entry selection.id", nonempty: true)
  assert(id in profile.entries, message: "Unknown selected entry: " + id)
  let entry = object(profile.entries.at(id), "entry " + id)
  let ids = if "claims" in selection { selection.claims } else { entry.at("claims", default: ()) }
  (
    id: id,
    title: string-value(required(entry, "title", "entry " + id), "entry " + id + ".title", nonempty: true),
    subtitle: string-value(entry.at("subtitle", default: ""), "entry " + id + ".subtitle"),
    date: string-value(entry.at("date", default: ""), "entry " + id + ".date"),
    location: string-value(entry.at("location", default: ""), "entry " + id + ".location"),
    links: contacts(entry.at("links", default: ()), "entry " + id + ".links"),
    claims: resolve-claims(ids, profile, "cv", "entry " + id + " selected claims"),
  )
}
#let resolve-sections(raw, profile) = {
  array-value(raw, "application.sections").map(section => {
    let _ = object(section, "section")
    let title = string-value(required(section, "title", "section"), "section.title")
    let kind = choice(required(section, "kind", "section"), ("entries", "bullets", "paragraphs", "compact"), "section.kind")
    let items = array-value(required(section, "items", "section"), "section.items")
    (
      title: title,
      kind: kind,
      items: if kind == "entries" { items.map(item => resolve-entry(item, profile)) }
        else { resolve-claims(items, profile, "cv", "section " + title + " items") },
    )
  })
}
// One-pass substitution does not reinterpret tokens appearing inside a replacement.
#let substitute(value, tokens) = value.replace(regex("\\{(candidate|company|role)\\}"), match => tokens.at(match.captures.at(0)))
#let substitute-rich(value, tokens) = {
  if type(value) == str { substitute(value, tokens) }
  else { value.map(run => { let result = run; result.text = substitute(run.text, tokens); result }) }
}
#let resolve-letter(raw, profile) = {
  let _ = object(raw, "application.letter")
  let company = string-value(required(raw, "company", "letter"), "letter.company", nonempty: true)
  let role = string-value(required(raw, "role", "letter"), "letter.role", nonempty: true)
  let tokens = (candidate: profile.person.name, company: company, role: role)
  let recipient = none
  if "recipient" in raw {
    let record = object(raw.recipient, "letter.recipient")
    recipient = (
      name: substitute(string-value(record.at("name", default: ""), "letter.recipient.name"), tokens),
      address: strings(record.at("address", default: ()), "letter.recipient.address").map(line => substitute(line, tokens)),
    )
  }
  let paragraphs = array-value(required(raw, "paragraphs", "letter"), "letter.paragraphs")
  assert(paragraphs.len() > 0, message: "letter.paragraphs must not be empty")
  paragraphs = paragraphs.map(paragraph => {
    let _ = object(paragraph, "letter paragraph")
    let refs = strings(required(paragraph, "claim_refs", "letter paragraph"), "letter paragraph.claim_refs", nonempty: true)
    assert(refs.len() > 0, message: "Each letter paragraph requires canonical candidate claim_refs")
    (
      text: substitute-rich(rich-text(required(paragraph, "text", "letter paragraph"), "letter paragraph.text"), tokens),
      claims: resolve-claims(refs.dedup(), profile, "letter", "letter paragraph.claim_refs"),
    )
  })
  (
    company: substitute(company, tokens),
    role: substitute(role, tokens),
    recipient: recipient,
    subject: substitute(string-value(raw.at("subject", default: ""), "letter.subject"), tokens),
    date: substitute(string-value(raw.at("date", default: ""), "letter.date"), tokens),
    salutation: substitute(string-value(required(raw, "salutation", "letter"), "letter.salutation"), tokens),
    closing: substitute(string-value(required(raw, "closing", "letter"), "letter.closing"), tokens),
    paragraphs: paragraphs,
  )
}
#let read-root-json(path, where) = {
  let _ = string-value(path, where, nonempty: true)
  assert(path.starts-with("/"), message: where + " must be a /project-root-relative path")
  object(json(path), where)
}
#let load-document(profile-path, application-path, theme-path, surface: none) = {
  let _ = choice(surface, ("cv", "letter"), "surface")
  let profile = read-root-json(profile-path, "profile")
  let application = read-root-json(application-path, "application")
  let theme = read-root-json(theme-path, "theme")
  version-one(profile, "profile")
  version-one(application, "application")
  let is-example = boolean(required(profile, "is_example", "profile"), "profile.is_example")
  profile.insert("is_example", is-example)
  for field in ("sources", "claims", "entries") { let _ = object(required(profile, field, "profile"), "profile." + field) }
  let person = object(required(profile, "person", "profile"), "profile.person")
  person = (
    name: string-value(required(person, "name", "person"), "person.name", nonempty: true),
    headline: string-value(person.at("headline", default: ""), "person.headline"),
    contacts: contacts(person.at("contacts", default: ()), "person.contacts"),
  )
  profile.person = person
  let id = string-value(required(application, "id", "application"), "application.id")
  assert(id.len() <= 64 and id.match(regex("^[a-z0-9]+(?:-[a-z0-9]+)*$")) != none,
    message: "application.id must be a lowercase ASCII slug of at most 64 characters")
  (
    surface: surface,
    application_id: id,
    is_example: is-example,
    person: person,
    theme: resolve-theme(theme, surface),
    summary: if surface == "cv" { resolve-claims(application.at("summary", default: ()), profile, surface, "application.summary") } else { () },
    sections: if surface == "cv" { resolve-sections(application.at("sections", default: ()), profile) } else { () },
    letter: if surface == "letter" { resolve-letter(required(application, "letter", "application"), profile) } else { none },
  )
}
