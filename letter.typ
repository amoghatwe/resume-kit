#import "lib/document.typ": load-document
#import "lib/render.typ": render-letter

// Content and layout remain separate seams; both are editable native source.
#let resolved = load-document(
  sys.inputs.at("profile", default: "/examples/profile.json"),
  sys.inputs.at("application", default: "/examples/applications/general.json"),
  sys.inputs.at("theme", default: "/themes/classic.json"),
  surface: "letter",
)
#render-letter(resolved)
