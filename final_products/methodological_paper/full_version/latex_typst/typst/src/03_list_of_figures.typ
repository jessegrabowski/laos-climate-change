#set heading(numbering: none)
#show heading.where(level: 1): it => {
  it
  v(-1.5em)
}

= *List of Figures*
#outline(title: [],
        target: figure.where(kind: image),
      )

#pagebreak()
