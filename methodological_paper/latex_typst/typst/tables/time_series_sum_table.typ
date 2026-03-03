#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)


#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (2fr, 1.3fr, 1fr, 1fr, 1.4fr, 1fr, 1.3fr, 1fr, 1fr),
    rows: (auto, 2pt, ) + (auto, ) * 10,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [Statistic], [real_gdp_CRI], [Pop_CRI], [precip_CRI], [real_gdp_LAO], [Pop_LAO], [precip_LAO], [co2], [Temp],
    hlinex(stroke: black + 0.5pt),
    [],[],[],[],[],[],[],[],[],
    [Count], [44.00], [44.00], [40.00], [40.00], [44.00], [40.00], [45.00], [45.00],
    [Mean], [-0.00], [-0.00], [0.00], [-0.00], [0.00], [0.00], [-0.00], [0.00],
    [Standard Deviation], [1.01], [1.01], [1.01], [1.01], [1.01], [1.01], [1.01], [1.01],
    [Minimum], [-1.77], [-2.03], [-1.50], [-1.64], [-1.95], [-1.92], [-1.57], [-1.53],
    [25th Percentile], [-0.85], [-0.79], [-0.81], [-0.70], [-0.77], [-0.71], [-0.83], [-0.94],
    [Median], [-0.02], [0.24], [-0.07], [-0.39], [0.17], [0.02], [-0.10], [-0.10],
    [75th Percentile], [1.02], [0.88], [0.72], [1.11], [0.83], [0.93], [0.82], [0.73],
    [Maximum], [1.58], [1.26], [1.94], [1.50], [1.47], [1.68], [1.85], [1.95],
    [Kurtosis], [-1.23], [-0.99], [-0.97], [-1.43], [-0.99], [-0.97], [-1.15], [-1.11],
    [Skewness], [-0.15], [-0.52], [0.32], [0.27], [-0.40], [-0.21], [0.20], [0.30],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Descriptive Statistics of time series],
    note: [This table presents descriptive statistics climate time series included in the model. The series have been standardized, and the first then their first difference was computes ]
  ),
  kind: table,
)<time_series_sum>
