#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)


#figure(
  tablex(
    columns: (1fr,) * 2,
    rows: (auto, 2pt, ) + (auto, ) * 10,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [*Statistic*], [*Value*],
    hlinex(stroke: black + 0.5pt),
    [], [],
    [Count], [5818.00],
    [Mean], [0.79],
    [Standard Deviation], [1.83],
    [Minimum], [0.00],
    [25th Percentile], [0.00],
    [Median], [0.00],
    [75th Percentile], [1.00],
    [Maximum], [28.00],
    [Kurtosis], [54.00],
    [Skewness], [5.90],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Summary Statistics of Hydrological Disasters],
    note: [This table presents the summary statistics for hydrological disaster data, including count, mean, standard deviation, percentiles, and measures of kurtosis and skewness.]
  ),
  kind: table,
)
