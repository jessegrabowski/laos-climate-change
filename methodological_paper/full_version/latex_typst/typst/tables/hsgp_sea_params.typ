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
    [ell_log__[0]], [-0.54], [0.10], [2027.00], [2569.00], [1.00],
    [ell_log__[1]], [-0.62], [0.08], [2375.00], [3180.00], [1.00],
    [eta], [4.99], [0.36], [1376.00], [2432.00], [1.00],
    [eta_log__], [1.60], [0.07], [1376.00], [2432.00], [1.00],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Summary Statistics of Model Parameters for HSGP estimation in Cambodia, Thailand, Laos and Vietnam],
    note: []
  ),
  kind: table,
)
