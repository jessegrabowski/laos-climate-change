#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (1fr,) * 4,
    rows: (auto, 2pt, ) + (auto, ) * 11,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: .5pt + gray,
    hlinex(stroke: black + 3pt),
    [], [Drought], [Flood], [Storm],
    hlinex(stroke: black + 0.5pt),
    colspanx(4)[],
    hlinex(stroke: black + 0.5pt),
    [count], [3.0], [22.0], [8.0],
    [mean], [0.1], [0.8], [0.3],
    [std], [0.3], [0.6], [0.5],
    [min], [0.0], [0.0], [0.0],
    [25%], [0.0], [0.2], [0.0],
    [50%], [0.0], [1.0], [0.0],
    [75%], [0.0], [1.0], [0.8],
    [max], [1.0], [2.0], [2.0],
    [kurtosis], [4.9], [-0.2], [2.1],
    [skewness], [2.6], [0.1], [1.6],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Descriptive Statistics for disasters in Laos],
    note: [This table presents descriptive statistics for  drought, flood, and storm. Other events excluded due to non occurrence]
  ),
  kind: table,
)<event_count_table_laos>
