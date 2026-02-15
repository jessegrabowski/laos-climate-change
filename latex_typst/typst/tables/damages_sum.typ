#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (2fr, 1fr),
    rows: (auto, 2pt, ) + (auto, ) * 10,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [Statistic], [Total_Damage_Adjusted],
    hlinex(stroke: black + 0.5pt),
    [], [],
    [Count], [2300.00],
    [Mean], [1721.12],
    [Standard Deviation], [8233.07],
    [Minimum], [0.00],
    [25th Percentile], [25.32],
    [Median], [172.87],
    [75th Percentile], [848.19],
    [Maximum], [261939.92],
    [Kurtosis], [507.95],
    [Skewness], [19.01],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Summary Statistics of Total Damage Adjusted],
    note: [This table presents the summary statistics for total damage adjusted in 2025 USD millions.]
  ),
  kind: table,
)
