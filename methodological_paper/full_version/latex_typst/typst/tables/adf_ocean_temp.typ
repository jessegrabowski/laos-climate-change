#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns:(2fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    rows: (auto, 2pt, ) + (auto, ) * 6,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: .5pt + gray,
    hlinex(stroke: black + 3pt),
    [Specification], [Coeff], [Statistic], [P-value],[Lags], [1%], [5%], [10%],
    hlinex(stroke: black + 0.5pt),
    colspanx(8)[],
    hlinex(stroke: black + 0.5pt),
    [Constant and Trend], [-2.814], [-9.996], [0.000], [2], [-4.105], [-3.480], [-3.168],
    [Constant], [0.038], [0.272], [0.786], [], [], [], [],
     [Trend], [-0.002], [-0.494], [0.623], [], [], [], [],
     [Constant Only], [-2.806,], [-10.047], [0.000], [2], [-3.535], [-2.907], [-2.591],
     [Constant], [-0.022], [-0.321], [0.749], [], [], [], [],
    [No Constant], [-2.803], [-10.115],[ 0.000], [2], [-2.601],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Augmented Dickey Fuller test results for deviation from trend ocean temperature],
     note: [This table presents the results of the Augmented Dickey-Fuller (ADF) test for the deviation from trend of ocean temperature data. The ADF test checks for a unit root in the time series, indicating non-stationarity. The table includes different model specifications with their coefficient estimates, test statistics, p-values, and critical values at the 1%, 5%, and 10% significance levels. ]
  ),
  kind: table,
)<adf_ocean_tem>
