#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (1.5fr, 1.2fr, 1fr, 1.5fr, 1fr, 1fr, 1fr),
    rows: (auto, 2pt, ) + (auto, ) * 10,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [Statistic], [ln_pop_density], [ln_gdp_pc], [square_ln_gdp_pc], [precip_dev], [co2], [population],
    hlinex(stroke: black + 0.5pt),
    [], [], [], [], [], [], [],
    [Count], [2300.00], [2300.00], [2300.00], [2300.00], [2300.00], [2300.00],
    [Mean], [0.00], [0.00], [0.00], [0.00], [0.00], [0.00],
    [Standard Deviation], [1.00], [1.00], [1.00], [1.00], [1.00], [1.00],
    [Minimum], [-3.28], [-2.46], [-1.99], [-4.69], [-1.99], [-0.69],
    [25th Percentile], [-0.64], [-0.68], [-0.69], [-0.37], [-0.85], [-0.64],
    [Median], [0.27], [-0.14], [-0.21], [-0.11], [0.01], [-0.51],
    [75th Percentile], [0.79], [0.57], [0.50], [0.27], [0.86], [-0.09],
    [Maximum], [2.08], [2.25], [2.48], [5.11], [1.74], [2.15],
    [Kurtosis], [0.59], [-0.47], [-0.30], [5.76], [-1.05], [-0.04],
    [Skewness], [-0.90], [0.39], [0.69], [1.08], [-0.06], [1.34],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Summary Statistics of damage model covariates],
    note: [All features have been standardized]
  ),
  kind: table,
)
