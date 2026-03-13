#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (2fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    rows: (auto, 2pt, ) + (auto, ) * 6,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [Return Years], [2000], [2010], [2018], [2030], [2045], [2055],
    hlinex(stroke: black + 0.5pt),
    [], [], [], [], [], [], [],
    [100 RY], [611.19], [511.82], [1195.83], [1187.81], [1623.36], [2133.86],
    [50 RY], [307.86], [188.15], [581.92], [493.46], [864.37], [997.77],
    [10 RY], [23.38], [11.46], [52.44], [57.22], [90.29], [117.28],
    [4 RY], [0.72], [0.00], [3.47], [5.39], [10.58], [13.53],
    [2 RY], [0.00], [0.00], [0.00], [0.00], [0.00], [0.00],
    [1 RY], [0.00], [0.00], [0.00], [0.00], [0.00], [0.00],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Projected Return Year Values by Year for Lao],
    note: [This table presents return year values for the specified years in 2025 USD millions.]
  ),
  kind: table,
)
