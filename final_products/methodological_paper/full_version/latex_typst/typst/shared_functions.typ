#let in-outline = state("in-outline", false)

#let title = "Estimating Climate Change Risk Exposure: a probabilistic approach"

#let authors = (
            (name: "Camilo Saldarriaga",
                        extra: "",
                        affiliation: "ESCP Business School",
                        email:"jcamsalda@gmail.com"
                      ),

              (name: "Jesse Grabowski",
              extra: "",
              affiliation: "Paris-1 Panthéon-Sorbonne",
              email: "jessegrabowski@gmail.com"
              ),

              (name: "Jan Rielaender",
              extra: "",
              affiliation: "OECD Development Center",
              email:"Jan.RIELAENDER@oecd.org"
            ),


            )
#let codes= ("Q54", "Q51", "C11", "C150", "C53", "Q56", "D81")

#let keywords = ("Climate change risk", "Bayesian modeling", "hydrometeorological disasters", "geo-spatial modeling", "probabilistic risk assessment", "damage curves", "uncertainty quantification")

#let title_and_note(title: str, note: [], short_title: []) = {
  context if in-outline.get() {
    if short_title == [] {
      title
    }
    else {
      short_title
    }
  }
  else {
  strong(title) + [\ ] + text(note, size:9pt)
  }
}


#let in-outline = state("in-outline", false)
#set par(justify: false)

#let OECD_blue = rgb("#dbe5f1")

#let title_and_note(title: str, note: [], short_title: []) = {
  context if in-outline.get() {
    if short_title == [] {
      title
    }
    else {
      short_title
    }
  }
  else {
  strong(title) + [\ ] + text(note, size:9pt)
  }
}
