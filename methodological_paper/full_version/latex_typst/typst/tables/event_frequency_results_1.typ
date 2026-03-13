#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note
#set text(size: 8pt)
#set par(justify: false)
#figure(
  tablex(
    columns: (6fr, 3fr, 2fr, 2fr, 2fr, 2fr, 2fr),
    rows: (auto, 2pt, ) + (auto, ) * 20,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [Parameter], [mean], [sd], [hdi_3%], [hdi_97%], [ess_tail], [r_hat],
    hlinex(stroke: black + 0.5pt),
    [], [], [], [],[], [],[],
    [alpha], [10.923], [1.575], [8.076], [13.839], [6169.0], [1.0],
    [alpha_X[ln_population_density]], [0.002], [2.400], [-4.666], [4.614], [6163.0], [1.0],
    [alpha_X[ln_gdp_pc]], [-0.047], [2.429], [-4.824], [4.463], [6167.0], [1.0],
    [alpha_X[precip_deviation]], [0.002], [2.351], [-4.368], [4.521], [6562.0], [1.0],
    [alpha_X[co2]], [-0.006], [2.405], [-4.545], [4.826], [6275.0], [1.0],
    [alpha_X[population]], [0.043], [2.522], [-4.605], [4.951], [6086.0], [1.0],
    [alpha_X_loc[ln_population_density]], [-0.019], [1.007], [-1.927], [1.847], [5732.0], [1.0],
    [alpha_X_loc[ln_gdp_pc]], [-0.003], [1.005], [-1.897], [1.903], [5927.0], [1.0],
    [alpha_X_loc[precip_deviation]], [0.000], [0.981], [-1.833], [1.844], [6378.0], [1.0],
    [alpha_X_loc[co2]], [-0.001], [1.008], [-1.909], [1.881], [5888.0], [1.0],
    [alpha_X_loc[population]], [0.014], [1.000], [-1.777], [1.943], [6242.0], [1.0],
    [alpha_X_offset[ln_population_density]], [0.008], [0.907], [-1.770], [1.643], [5903.0], [1.0],
    [alpha_X_offset[ln_gdp_pc]], [-0.004], [0.898], [-1.637], [1.729], [6051.0], [1.0],
    [alpha_X_offset[precip_deviation]], [-0.007], [0.886], [-1.671], [1.692], [6037.0], [1.0],
    [alpha_X_offset[co2]], [-0.006], [0.885], [-1.650], [1.661], [5974.0], [1.0],
    [alpha_X_offset[population]], [0.010], [0.929], [-1.729], [1.739], [5775.0], [1.0],
    [alpha_X_scale[ln_population_density]], [1.996], [1.416], [0.037], [4.517], [4929.0], [1.0],
    [alpha_X_scale[ln_gdp_pc]], [2.001], [1.433], [0.051], [4.544], [5176.0], [1.0],
    [alpha_X_scale[precip_deviation]], [1.979], [1.398], [0.034], [4.452], [5291.0], [1.0],
    [alpha_X_scale[co2]], [1.989], [1.410], [0.051], [4.476], [4705.0], [1.0],
    [alpha_X_scale[population]], [2.002], [1.418], [0.033], [4.465], [4370.0], [1.0],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Summary Statistics 1 for frequency event model estimation ],
    note: [Variables contained: alpha and alpha_X]
  ),
  kind: table,
)
