#import "lib/document.typ": load-document
#import "lib/render.typ": render-cv

// Direct builds use visibly fictional examples. The CLI supplies workspace paths.
#let resolved = load-document(
  sys.inputs.at("profile", default: "/examples/profile.json"),
  sys.inputs.at("application", default: "/examples/applications/general.json"),
  sys.inputs.at("theme", default: "/themes/classic.json"),
  surface: "cv",
)
#render-cv(resolved)
