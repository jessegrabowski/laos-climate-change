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
    [100 RY], [1236.37], [2812.63], [1762.17], [3213.56], [6181.40], [6546.61],
    [50 RY], [533.97], [1351.89], [913.47], [1543.53], [3077.38], [3205.45],
    [10 RY], [32.49], [175.55], [89.65], [166.32], [338.13], [401.02],
    [4 RY], [0.00], [17.47], [6.14], [17.36], [37.31], [46.95],
    [2 RY], [0.00], [0.00], [0.00], [0.00], [0.00], [0.00],
    [1 RY], [0.00], [0.00], [0.00], [0.00], [0.00], [0.00],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Return Year Values by Year for Costa Rica],
    note: [This table presents return year values for the specified years in 2025 USD.]
  ),
  kind: table,
)
