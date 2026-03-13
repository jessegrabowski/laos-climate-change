#import "@preview/subpar:0.1.1"
#import "shared_functions.typ": in-outline, title, authors, keywords

#set math.equation(numbering: "(1)")
#set heading(numbering: "1.1")

#set par(leading: 1em,
         first-line-indent: 1.8em,
         justify: true)
#set text(font:"TeX Gyre Heros",
          size:11pt,
          hyphenate: false)

#show raw: set text(font: "New Computer Modern Mono")

#show heading: set block(above: 1.4em, below: 1em)

#show heading.where(level: 1): it => {
    set text(28pt, fill:rgb("#4472C4"))
    it
    ""
    v(-1.5em)
}

#show heading.where(level: 2): it => {
    set text(12pt, fill:rgb("#4472C4"))
    ""
    it
    ""
    v(-1em)
}



#show outline: it => {
  in-outline.update(true)
  it
  in-outline.update(false)
}

#show footnote.entry: set align(left)
#set footnote.entry(indent: 0cm, gap: 0.5cm)

#show: set figure.caption(position: top)

#show figure.caption: it => [
  #text(size: 9pt)[#par(leading: 0.5em, first-line-indent: 1em)[#align(center)[#strong([#it.supplement #context it.counter.display(it.numbering).]) #it.body]
]]
]

#show figure: it => {
    it
    ""
    v(-1em)
}

#set document(title: title,
              author: authors.map(d => d.name).join(", "),
              keywords: keywords,
              date: auto)

#set page(numbering: (..numbers) => {
  if numbers.pos().at(0) != 1 {
    numbering("i", numbers.pos().at(0))
  }
})

#include "src/01_title_page.typ"
#include "src/02_table_of_contents.typ"
#include "src/03_list_of_figures.typ"
#include "src/04_list_of_tables.typ"

#set page(numbering: "1")
#counter(page).update(1)

#include "src/05_introduction.typ"
#include "src/06_literature_review.typ"
#include "src/07_modeling_approach.typ"
#include "src/08_methodology.typ"
#include "src/09_data.typ"
#include "src/10_results.typ"
#include "src/11_conclusions.typ"




#bibliography("references.bib",
              style: "harvard-cite-them-right",
              title: "References")

#include "src/annex_1.typ"
#include "src/annex_2.typ"
