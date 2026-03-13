#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (1.3fr, 1.5fr, 1.8fr, 2fr, 1.5fr, 1.3fr, 1.5fr, 2.2fr, 2.1fr, 1.6fr),
    rows: (auto, 2pt, ) + (auto, ) * 10,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [Statistic], [is_disaster], [log_dist_river], [log_dist_coast], [Population], [co2], [precip_dev], [dev_ocean_temp], [log_pop_density], [log_gdp_per_cap],
    hlinex(stroke: black + 0.5pt),
    [], [],[], [],[], [],[], [],[], [],
    [Count], [30030.00], [30030.00], [30030.00], [30030.00], [30030.00], [30030.00], [30030.00], [30030.00], [30030.00],
    [Mean], [0.06], [0.00], [0.00], [0.00], [-0.00], [-0.00], [-0.00], [-0.00], [-0.00],
    [Standard Deviation], [0.23], [1.00], [1.00], [1.00], [1.00], [1.00], [1.00], [1.00], [1.00],
    [Minimum], [0.00], [-7.92], [-8.83], [-2.35], [-1.66], [-2.48], [-2.35], [-3.44], [-1.92],
    [25th Percentile], [0.00], [-0.46], [-0.49], [-0.27], [-0.88], [-0.74], [-0.71], [-0.42], [-0.81],
    [Median], [0.00], [0.22], [0.29], [0.21], [-0.07], [-0.01], [-0.09], [-0.03], [0.02],
    [75th Percentile], [0.00], [0.69], [0.75], [0.61], [0.80], [0.65], [0.91], [0.82], [0.82],
    [Maximum], [1.00], [1.66], [1.30], [1.49], [1.86], [2.81], [1.95], [1.28], [1.62],
    [Kurtosis], [13.13], [3.35], [3.36], [0.44], [-1.13], [-0.00], [-0.46], [1.52], [-1.11],
    [Skewness], [3.89], [-1.46], [-1.57], [-1.05], [0.20], [0.40], [-0.01], [-1.17], [-0.17],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Summary Statistics of the geo-spatial model data set for Cambodia, Thailand, Laos and Vietnam],
    note: [All features, except for "is_disaster" have been standardized]
  ),
  kind: table,
)
