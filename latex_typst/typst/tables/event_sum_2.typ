#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note
#set text(size: 8pt)
#set par(justify: false)
#figure(
  tablex(
    columns: (3fr,3.5fr, 2fr, 2fr, 2fr, 3fr),
    rows: (auto, 2pt, ) + (auto, ) * 10,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [Statistic], [ln_population_density], [ln_gdp_pc], [co2], [population], [precip_deviation],
    hlinex(stroke: black + 0.5pt),
    [], [], [], [], [], [],
    [Count], [5737.00], [5737.00], [5737.00], [5737.00], [5737.00],
    [Mean], [3.81], [8.18], [374.92], [41.23], [0.34],
    [Standard Deviation], [1.33], [1.46], [21.31], [140.71], [171.03],
    [Minimum], [0.12], [5.10], [340.12], [0.12], [-1477.12],
    [25th Percentile], [2.94], [7.05], [356.54], [3.69], [-69.37],
    [Median], [4.01], [8.09], [373.45], [9.45], [-1.17],
    [75th Percentile], [4.68], [9.20], [391.85], [28.34], [69.37],
    [Maximum], [7.15], [11.64], [414.21], [1411.10], [1576.26],
    [Kurtosis], [-0.17], [-0.86], [-1.12], [60.62], [8.96],
    [Skewness], [-0.40], [0.23], [0.17], [7.53], [0.09],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Summary Statistics of event model covariates],
    note: []
  ),
  kind: table,
)
