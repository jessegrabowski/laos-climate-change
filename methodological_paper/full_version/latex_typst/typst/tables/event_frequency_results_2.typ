#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note
#set text(size: 8pt)
#set par(justify: false)
#figure(
  tablex(
    columns: (7fr, 2fr, 2fr, 2fr, 2fr, 2fr, 2fr),
    rows: (auto, 2pt, ) + (auto, ) * 17,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [Statistic], [mean], [sd], [hdi_3%], [hdi_97%], [ess_tail], [r_hat],
    hlinex(stroke: black + 0.5pt),
    [], [], [], [], [], [], [],
    [beta[ln_population_density]], [0.338], [0.108], [0.140], [0.544], [4237.0], [1.00],
    [beta[ln_gdp_pc]], [-0.651], [0.088], [-0.813], [-0.478], [3745.0], [1.00],
    [beta[precip_deviation]], [0.002], [0.000], [0.002], [0.003], [6027.0], [1.00],
    [beta[co2]], [0.025], [0.002], [0.022], [0.029], [4213.0], [1.00],
    [beta[population]], [0.010], [0.001], [0.008], [0.012], [5081.0], [1.00],
    [beta_GY[ln_population_density]], [-0.548], [0.306], [-1.119], [0.010], [1263.0], [1.01],
    [beta_GY[ln_gdp_pc]], [-0.559], [0.298], [-1.120], [-0.001], [945.0], [1.01],
    [beta_GY[precip_deviation]], [-0.574], [0.307], [-1.143], [-0.010], [1017.0], [1.03],
    [beta_GY[co2]], [-0.526], [0.305], [-1.092], [0.048], [846.0], [1.02],
    [beta_GY[population]], [-0.550], [0.295], [-1.074], [0.027], [1468.0], [1.01],
    [country_loc], [-3.935], [0.644], [-5.203], [-2.784], [4829.0], [1.00],
    [country_scale], [0.340], [0.193], [0.024], [0.686], [3321.0], [1.00],
    [rho], [0.878], [0.138], [0.595], [1.000], [1132.0], [1.01],
    [sigma_X[ln_population_density]], [1.004], [0.993], [0.000], [2.865], [3529.0], [1.00],
    [sigma_X[ln_gdp_pc]], [1.002], [1.016], [0.000], [2.843], [3382.0], [1.00],
    [sigma_X[precip_deviation]], [1.006], [1.010], [0.000], [2.868], [3393.0], [1.00],
    [sigma_X[co2]], [0.996], [0.984], [0.000], [2.777], [3547.0], [1.00],
    [sigma_X[population]], [1.006], [1.023], [0.000], [2.896], [3314.0], [1.00],
    [zero_prob], [0.998], [0.002], [0.994], [1.000], [3568.0], [1.00],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Summary Statistics 2 for frequency event model estimation],
    note: []
  ),
  kind: table,
)
