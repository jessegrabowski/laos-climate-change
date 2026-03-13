#show outline.entry: it => {
  text(13pt, it)
}

#show outline.entry.where(
  level: 1
): set outline.entry(fill: none)

#show outline.entry.where(
  level: 1
): it => {
  v(14pt, weak: true)
  strong(it)
}

#outline(title: [Contents],
        indent: 3em,
      )

#pagebreak()
