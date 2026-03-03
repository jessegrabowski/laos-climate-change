#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note
#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (2fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    rows: (auto, 2pt, ) + (auto, ) * 5,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [Parameter], [mean], [sd], [ess_bulk], [ess_tail], [r_hat],
    hlinex(stroke: black + 0.5pt),
    [], [], [], [], [],[],
    [ell_log__[0]], [-0.40], [0.11], [758.00], [1540.00], [1.01],
    [ell_log__[1]], [-0.09], [0.11], [673.00], [1566.00], [1.01],
    [eta], [3.81], [0.40], [540.00], [1223.00], [1.01],
    [eta_log__], [1.33], [0.10], [540.00], [1223.00], [1.01],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Summary Statistics of Model Parameters for HSGP estimation in Central America],
    note: []
  ),
  kind: table,
)
