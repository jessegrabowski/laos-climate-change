#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (2fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    rows: (auto, 2pt, ) + (auto, ) * 6,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: .5pt + gray,
    hlinex(stroke: black + 3pt),
    [Specification], [Coeff], [Statistic], [P-value], [Lags], [1%], [5%], [10%],
    hlinex(stroke: black + 0.5pt),
    colspanx(8)[],
    hlinex(stroke: black + 0.5pt),
    [Constant and Trend], [-1.866], [-10.979], [0.000], [1], [-4.108], [-3.481], [-3.168],
    [Constant], [-0.031], [-0.557], [0.579], [], [], [], [],
    [Trend], [-0.000], [-0.034], [0.973], [], [], [], [],
    [Constant Only], [-1.866], [-11.091], [0.000], [1], [-3.537], [-2.908], [-2.591],
    [Constant], [-0.032], [-1.188], [0.240], [], [], [], [],
    [No Constant], [-1.839], [-10.995], [0.000], [1], [-2.602], [-1.946], [-1.613],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Augmented Dickey Fuller test results for de-trended CO2],
    note: [This table presents the results of the Augmented Dickey-Fuller (ADF) test for de-trended CO2 data. The ADF test checks for a unit root in the time series, indicating non-stationarity. The table includes different model specifications with their coefficient estimates, test statistics, p-values, and critical values at the 1%, 5%, and 10% significance levels. ]
  ),
  kind: table,
)<adf_co2>
