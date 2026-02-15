#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (1fr,) * 6,
    rows: (auto, 2pt, ) + (auto, ) * 11,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: .5pt + gray,
    hlinex(stroke: black + 3pt),
    [], [Drought], [Extreme temperature], [Flood], [Storm], [Wildfire],
    hlinex(stroke: black + 0.5pt),
    colspanx(6)[],
    hlinex(stroke: black + 0.5pt),
    [count], [489.00], [111.00], [2305.00], [1098.00], [137.00],
    [mean], [1.02], [1.07], [1.68], [1.77], [1.13],
    [std], [0.16], [0.26], [1.53], [1.71], [0.45],
    [min], [1.00], [1.00], [1.00], [1.00], [1.00],
    [25%], [1.00], [1.00], [1.00], [1.00], [1.00],
    [50%], [1.00], [1.00], [1.00], [1.00], [1.00],
    [75%], [1.00], [1.00], [2.00], [2.00], [1.00],
    [max], [3.00], [2.00], [23.00], [15.00], [4.00],
    [kurtosis], [68.40], [9.43], [40.91], [14.84], [17.30],
    [skewness], [7.86], [3.35], [5.10], [3.46], [3.98],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Descriptive Statistics of Environmental Events],
    note: []
  ),
  kind: table,
)<events_sum_table_a>
