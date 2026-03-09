#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note
#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (3fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    rows: (auto, 2pt, ) + (auto, ) * 4,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [Location], [2000], [2010], [2018], [2030], [2045],
    hlinex(stroke: black + 0.5pt),
    [], [], [], [], [], [],
    [Desamparados (San José)], [0.0034], [0.0094], [0.0065], [0.0086], [0.0105],
    [El Bambú (Filadelfia, Guanacaste)], [0.0019], [0.0048], [0.0033], [0.0050], [0.0065],
    [Cariari (Pococí, Limón)], [0.0006], [0.0017], [0.0012], [0.0017], [0.0027],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Projected probability of a disaster on selected locations in Costa Rica trough time],
    note: [The table presents the probability in percentages of one event happening on the selected point at the given yar]
  ),
  kind: table,
)
