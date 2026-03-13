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
    [Constant and Trend], [-0.852], [-5.329], [0.000], [0], [-4.212], [-3.530], [-3.196],
    [Constant], [151085.793], [5.295], [0.000], [], [], [], [],
    [Trend], [122.344], [1.462], [0.152], [], [], [], [],
    [Constant Only], [-0.800], [-5.055], [0.000], [0], [-3.610], [-2.939], [-2.608],
    [Constant], [144073.318], [5.045], [0.000], [], [], [], [],
    [No Constant], [-0.001], [-0.108], [0.647], [1], [-2.627], [-1.950], [-1.611],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Augmented Dickey Fuller test results for deviation from world precipitation],
    note: [This table presents the results of the Augmented Dickey-Fuller (ADF) test for the deviation from world precipitation data data. The ADF test checks for a unit root in the time series, indicating non-stationarity. The table includes different model specifications with their coefficient estimates, test statistics, p-values, and critical values at the 1%, 5%, and 10% significance levels. ]
  ),
  kind: table,
)<adf_precip>
