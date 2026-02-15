#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 7.5pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (1.3fr, 1.5fr, 1.8fr, 1.8fr, 1.5fr, 1.3fr, 1.5fr, 2.2fr, 2.1fr, 1.6fr),
    rows: (auto, 2pt, ) + (auto, ) * 10,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [Statistic], [is_disaster], [log_dist_river], [log_dist_coast], [Population], [co2], [precip_dev], [dev_ocean_temp], [log_pop_density], [log_gdp_per_cap],
    hlinex(stroke: black + 0.5pt),
    [], [],[], [],[], [],[], [],[], [],
    [Count], [22092.00], [22092.00], [22092.00], [22092.00], [22092.00], [22092.00], [22092.00], [22092.00], [22092.00],
    [Mean], [0.04], [-0.00], [-0.00], [0.00], [0.00], [0.00], [-0.00], [-0.00], [0.00],
    [Standard Deviation], [0.20], [1.00], [1.00], [1.00], [1.00], [1.00], [1.00], [1.00], [1.00],
    [Minimum], [0.00], [-10.09], [-7.73], [-1.31], [-1.72], [-1.60], [-2.28], [-1.59], [-2.77],
    [25th Percentile], [0.00], [-0.44], [-0.45], [-0.72], [-0.77], [-0.82], [-0.73], [-0.83], [-0.68],
    [Median], [0.00], [0.23], [0.24], [-0.30], [-0.07], [-0.15], [-0.06], [-0.05], [-0.06],
    [75th Percentile], [0.00], [0.68], [0.74], [0.53], [0.56], [0.76], [0.94], [0.80], [0.64],
    [Maximum], [1.00], [2.38], [1.29], [2.72], [2.21], [2.44], [1.96], [1.83], [2.79],
    [Kurtosis], [18.78], [3.95], [4.13], [0.36], [-0.30], [-0.53], [-0.61], [-1.13], [-0.11],
    [Skewness], [4.56], [-1.55], [-1.65], [1.13], [0.60], [0.62], [0.05], [0.16], [0.11],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Summary Statistics of the geo-spatial model data set for  Central America],
    note: [All features, except for "is_disaster" have been standardized]
  ),
  kind: table,
)



#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)
