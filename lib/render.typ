// The layout seam consumes only the resolved document. Edit this original native
// implementation for layouts beyond the JSON theme; no packages are required.

// Measured cluster spacing for a 10 pt body on A4 with a 20 pt name and an 11 pt
// section heading. The theme owns body leading, paragraph and list spacing plus
// the entry and section boundary tokens; these values fix the header, heading and
// bullet clusters that the JSON surface does not express. They are absolute
// because a relative theme length cannot be offset arithmetically here.
#let name-contact-gap = 13.1pt  // renders 8.63pt, matching the reference's 8.63pt
#let heading-rule-gap = 1.77pt  // renders 1.92pt to the rule, matching the reference's 1.92pt
#let rule-content-gap = 5.95pt  // renders 5.28-5.76pt, matching the reference's 5.28-5.76pt
#let bullet-body-indent = 5pt    // bullet marker advance to the bullet text column
#let entry-boundary-boost = 5.75pt  // added to theme.spacing.entry for a 7.7 pt entry boundary
#let section-boundary-boost = 1.9pt  // added to theme.spacing.section for a 7.7 pt section boundary

#let rich(value) = {
  if type(value) == str { text(value) }
  else {
    for run in value {
      let body = text(run.text)
      if run.bold { body = strong(body) }
      if run.italic { body = emph(body) }
      if run.url != none { body = link(run.url, body) }
      body
    }
  }
}
#let has-text(value) = {
  if type(value) == str { value.trim() != "" }
  else { value.any(run => run.text.trim() != "") }
}
#let claim-body(claim) = [
  #rich(claim.text)#if has-text(claim.qualifier) { [ #rich(claim.qualifier)] }
]
#let contact-body(contact) = {
  if contact.url == none { text(contact.text) }
  else { link(contact.url, text(contact.text)) }
}
#let identity(document) = {
  let theme = document.theme
  // The measured gaps below are reference geometry for the CV surface only. The
  // letter keeps its own theme-driven identity spacing.
  let cv = document.surface == "cv"
  block(above: 0pt,
    below: if cv { calc.abs(theme.spacing.section) + section-boundary-boost } else { theme.spacing.section },
    breakable: false)[
    // The width must be stated. An auto-width align block shrink-wraps to its
    // widest child, so every row centred inside that box instead of the page
    // measure and the whole header sat about 83 pt left of the page centre. This
    // fix, like the removal of the fictional marker, applies to both surfaces.
    #align(theme.header_alignment, block(width: 100%)[
      #show heading: set block(above: 0pt,
        below: if cv { name-contact-gap } else { theme.spacing.paragraph })
      #heading(level: 1, outlined: false, bookmarked: false, text(document.person.name))
      #if document.person.headline != "" { block(above: 0pt, below: theme.spacing.paragraph, text(document.person.headline)) }
      #if document.person.contacts.len() > 0 {
        block(above: 0pt, below: 0pt,
          document.person.contacts.map(contact-body).join(text(theme.contact_separator)))
      }
    ])
  ]
}
#let entry-links(links, theme) = links.map(contact-body).join(text(theme.contact_separator))
#let entry-details(entry) = (entry.subtitle, entry.location).filter(value => value != "").join(" · ")

// Title, date right-aligned on the same row, subtitle and location on the next
// row, links on their own following row. The default for every selection.
#let standard-entry(entry, theme) = {
  block(above: 0pt, below: theme.spacing.paragraph, sticky: true)[
    #strong(text(entry.title))#if entry.date != "" { [#h(1fr)#text(entry.date)] }
    #if entry-details(entry) != "" {
      linebreak()
      text(entry-details(entry))
    }
    #if entry.links.len() > 0 {
      linebreak()
      entry-links(entry.links, theme)
    }
  ]
}

// Institution and place on the first row, the italic qualification and the date
// on the second. Use where the subtitle is a degree or similar qualification.
#let education-entry(entry, theme) = {
  block(above: 0pt, below: theme.spacing.paragraph, sticky: true)[
    #strong(text(entry.title))#if entry.location != "" { [#h(1fr)#text(entry.location)] }
    #if entry.subtitle != "" or entry.date != "" {
      linebreak()
      if entry.subtitle != "" { emph(text(entry.subtitle)) }
      if entry.date != "" { [#h(1fr)#text(entry.date)] }
    }
    #if entry.links.len() > 0 {
      linebreak()
      entry-links(entry.links, theme)
    }
  ]
}

// Role and employer on one bold row with the date right-aligned, then the links
// row. Use where the title is an organisation and the subtitle is the job.
#let role-entry(entry, theme) = {
  block(above: 0pt, below: theme.spacing.paragraph, sticky: true)[
    #if entry.subtitle != "" { strong(text(entry.subtitle)) }
    #if entry.subtitle != "" and entry.title != "" { text(" · ") }
    #strong(text(entry.title))
    #if entry.date != "" { [#h(1fr)#text(entry.date)] }
    #if entry.links.len() > 0 {
      linebreak()
      entry-links(entry.links, theme)
    }
  ]
}

// Title, subtitle and links joined on one row with the date right-aligned. Use
// for short self-contained items such as projects and competition entries.
#let inline-entry(entry, theme) = {
  block(above: 0pt, below: theme.spacing.paragraph, sticky: true)[
    #strong(text(entry.title))
    #if entry.subtitle != "" { [ #text(" · ")#text(entry.subtitle)] }
    #if entry.links.len() > 0 { [ #text(" · ")#entry-links(entry.links, theme)] }
    #if entry.date != "" { [#h(1fr)#text(entry.date)] }
  ]
}

#let entry-body(entry, theme) = {
  if entry.layout == "education" { education-entry(entry, theme) }
  else if entry.layout == "role" { role-entry(entry, theme) }
  else if entry.layout == "inline" { inline-entry(entry, theme) }
  else { standard-entry(entry, theme) }
  if entry.claims.len() > 0 {
    list(..entry.claims.map(claim-body))
  }
}
#let section-heading(title, theme) = {
  block(above: calc.abs(theme.spacing.section) + section-boundary-boost,
    below: rule-content-gap, sticky: true)[
    #show heading: set block(above: 0pt, below: heading-rule-gap)
    #heading(level: 2, outlined: false, text(title))
    #if theme.heading_rules { line(length: 100%, stroke: theme.rule_width + theme.accent) }
  ]
}
#let section-body(section, theme) = {
  if section.items.len() > 0 {
    if section.title != "" { section-heading(section.title, theme) }
    if section.kind == "entries" {
      for (index, entry) in section.items.enumerate() {
        if index > 0 { v(calc.abs(theme.spacing.entry) + entry-boundary-boost) }
        entry-body(entry, theme)
      }
    } else if section.kind == "bullets" {
      list(..section.items.map(claim-body))
    } else if section.kind == "paragraphs" {
      for claim in section.items { block(above: 0pt, below: theme.spacing.paragraph, claim-body(claim)) }
    } else if section.kind == "compact" {
      block(above: 0pt, below: theme.spacing.paragraph,
        section.items.map(claim-body).join(text(theme.compact_separator)))
    }
  }
}
#let letter-body(document) = {
  let letter = document.letter
  let theme = document.theme
  if letter.date != "" { block(above: 0pt, below: theme.spacing.paragraph, text(letter.date)) }
  if letter.recipient != none {
    let lines = (letter.recipient.name,) + letter.recipient.address
    lines = lines.filter(value => value != "")
    if lines.len() > 0 { block(above: 0pt, below: theme.spacing.section, lines.map(text).join(linebreak())) }
  }
  if letter.subject != "" {
    block(above: 0pt, below: theme.spacing.section, strong(text(letter.subject)))
  }
  if letter.salutation != "" { block(above: 0pt, below: theme.spacing.paragraph, text(letter.salutation)) }
  for paragraph in letter.paragraphs {
    block(above: 0pt, below: theme.spacing.paragraph)[
      #rich(paragraph.text)#for claim in paragraph.claims {
        if has-text(claim.qualifier) { [ #rich(claim.qualifier)] }
      }
    ]
  }
  block(above: theme.spacing.section, below: 0pt)[
    #text(letter.closing)#linebreak()#text(document.person.name)
  ]
}
#let styled(data, body) = {
  let theme = data.theme
  set document(title: data.person.name + (if data.surface == "cv" { " — Resume" } else { " — Cover Letter" }), author: data.person.name)
  set text(font: theme.font, size: theme.sizes.body, lang: theme.language,
    dir: theme.direction, hyphenate: theme.hyphenate)
  set par(leading: theme.spacing.leading, spacing: theme.spacing.paragraph, justify: theme.justify)
  set align(theme.alignment)
  // The 5 pt marker-to-text gap is CV reference geometry; the letter keeps 1em.
  set list(indent: 0pt,
    body-indent: if data.surface == "cv" { bullet-body-indent } else { 1em },
    spacing: theme.spacing.list)
  set heading(numbering: none)
  show heading.where(level: 1): set text(size: theme.sizes.name, fill: theme.accent)
  show heading.where(level: 2): set text(size: theme.sizes.heading, fill: theme.accent)
  show heading: set block(above: 0pt, below: theme.spacing.paragraph)
  show link: set text(fill: theme.accent)
  let paper-settings = if type(theme.paper) == str { (paper: theme.paper) }
    else { (width: theme.paper.width, height: theme.paper.height) }
  set page(..paper-settings)
  set page(
    margin: theme.margins,
    footer: if theme.page_numbers {
      context align(center)[
        #set text(size: 8pt)
        #counter(page).display("1")
      ]
    } else { none },
  )
  identity(data)
  body
  // Native context sees the final layout, including pages added by custom source.
  context {
    let pages = counter(page).final().first()
    if theme.max_pages != none {
      assert(pages <= theme.max_pages,
        message: "Document has " + str(pages) + " pages; theme.max_pages is " + str(theme.max_pages)
          + ". Shorten the selected content or edit the theme page limit.")
    }
    [#metadata((pages: pages, application_id: data.application_id,
      surface: data.surface, is_example: data.is_example)) <resume-kit>]
  }
}
#let render-cv(document) = styled(document, [
  // The summary is a CV-only surface, so it carries the same heading and rule as
  // any titled section instead of running straight into the identity block.
  #if document.summary.len() > 0 { section-heading("Professional Summary", document.theme) }
  #for claim in document.summary {
    // A definite width is required for the same reason as the identity block: an
    // auto-width block wraps to its natural measure and its continuation lines
    // stay ragged instead of reaching the page measure.
    block(above: 0pt, below: document.theme.spacing.paragraph, width: 100%)[
      #set par(justify: true)
      #claim-body(claim)
    ]
  }
  #for section in document.sections { section-body(section, document.theme) }
])
#let render-letter(document) = styled(document, letter-body(document))
