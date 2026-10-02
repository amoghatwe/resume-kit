// The layout seam consumes only the resolved document. Edit this original native
// implementation for layouts beyond the JSON theme; no packages are required.

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
  block(above: 0pt, below: theme.spacing.section, breakable: false)[
    #align(theme.header_alignment)[
      #heading(level: 1, outlined: false, bookmarked: false, text(document.person.name))
      #if document.person.headline != "" { block(above: 0pt, below: theme.spacing.paragraph, text(document.person.headline)) }
      #if document.person.contacts.len() > 0 {
        block(above: 0pt, below: 0pt,
          document.person.contacts.map(contact-body).join(text(theme.contact_separator)))
      }
      #if document.is_example {
        block(above: theme.spacing.paragraph, below: 0pt,
          text(size: 8pt, fill: theme.accent, "FICTIONAL EXAMPLE — not a real candidate"))
      }
    ]
  ]
}
#let entry-body(entry, theme) = {
  block(above: 0pt, below: theme.spacing.paragraph, sticky: true)[
    #strong(text(entry.title))#if entry.date != "" { [#h(1fr)#text(entry.date)] }
    #if entry.subtitle != "" or entry.location != "" {
      linebreak()
      let details = (entry.subtitle, entry.location).filter(value => value != "")
      text(details.join(" · "))
    }
    #if entry.links.len() > 0 {
      linebreak()
      entry.links.map(contact-body).join(text(theme.contact_separator))
    }
  ]
  if entry.claims.len() > 0 {
    list(..entry.claims.map(claim-body))
  }
}
#let section-body(section, theme) = {
  if section.items.len() > 0 {
    if section.title != "" {
      block(above: theme.spacing.section, below: theme.spacing.paragraph, sticky: true)[
        #heading(level: 2, outlined: false, text(section.title))
        #if theme.heading_rules { line(length: 100%, stroke: theme.rule_width + theme.accent) }
      ]
    }
    if section.kind == "entries" {
      for (index, entry) in section.items.enumerate() {
        if index > 0 { v(theme.spacing.entry) }
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
  set list(indent: 0pt, body-indent: 1em, spacing: theme.spacing.list)
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
    footer: if data.is_example or theme.page_numbers {
      context align(center)[
        #set text(size: 8pt)
        #if data.is_example { text("FICTIONAL EXAMPLE — not a real candidate") }
        #if data.is_example and theme.page_numbers { text(" · ") }
        #if theme.page_numbers { counter(page).display("1") }
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
  #for claim in document.summary { block(above: 0pt, below: document.theme.spacing.paragraph, claim-body(claim)) }
  #for section in document.sections { section-body(section, document.theme) }
])
#let render-letter(document) = styled(document, letter-body(document))
