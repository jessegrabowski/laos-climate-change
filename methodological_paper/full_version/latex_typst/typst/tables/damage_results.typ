#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (4fr, 2fr, 2fr, 2fr, 2fr, 2fr, 2fr),
    rows: (auto, 2pt, ) + (auto, ) * 16,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [Parameter], [mean], [sd], [hdi_3%], [hdi_97%], [ess_tail], [r_hat],
    hlinex(stroke: black + 0.5pt),
    [], [],[],[],[],[],[],
    [alpha_X[ln_population_density]], [-0.470], [0.077], [-0.623], [-0.332], [280.0], [1.02],
    [alpha_X[ln_gdp_pc]], [-0.087], [0.073], [-0.224], [0.052], [376.0], [1.02],
    [alpha_X[precip_deviation]], [0.621], [0.086], [0.464], [0.781], [1489.0], [1.00],
    [alpha_X[co2]], [0.524], [0.086], [0.363], [0.680], [1366.0], [1.00],
    [alpha_X[population]], [-0.590], [0.075], [-0.730], [-0.447], [544.0], [1.01],
    [beta[ln_population_density]], [-1.047], [0.494], [-1.898], [-0.057], [3479.0], [1.00],
    [beta[ln_gdp_pc]], [0.413], [0.185], [0.062], [0.760], [3540.0], [1.00],
    [beta[precip_deviation]], [0.076], [0.036], [0.008], [0.142], [2549.0], [1.00],
    [beta[co2]], [0.040], [0.079], [-0.111], [0.184], [3116.0], [1.00],
    [beta[population]], [-0.075], [0.300], [-0.619], [0.511], [3245.0], [1.00],
    [beta_GX[ln_population_density]], [0.308], [0.010], [0.288], [0.328], [688.0], [1.03],
    [beta_GX[ln_gdp_pc]], [-0.007], [3.109], [-5.797], [5.695], [2366.0], [1.00],
    [beta_GX[precip_deviation]], [-0.007], [3.052], [-5.386], [6.063], [2445.0], [1.00],
    [beta_GX[co2]], [0.010], [3.015], [-5.790], [5.442], [2686.0], [1.00],
    [beta_GX[population]], [0.028], [2.993], [-5.584], [5.513], [3067.0], [1.00],
    [beta_GY[ln_population_density]], [0.282], [0.256], [-0.210], [0.753], [3415.0], [1.00],
    [beta_GY[ln_gdp_pc]], [-0.056], [0.231], [-0.503], [0.375], [3005.0], [1.00],
    [beta_GY[precip_deviation]], [-0.169], [0.230], [-0.635], [0.235], [2889.0], [1.00],
    [beta_GY[co2]], [-0.106], [0.235], [-0.552], [0.332], [2778.0], [1.00],
    [beta_GY[population]], [0.047], [0.242], [-0.397], [0.520], [2769.0], [1.00],
    [country_loc], [2.616], [0.301], [2.062], [3.185], [2102.0], [1.00],
    [country_scale], [0.145], [0.118], [0.000], [0.367], [1814.0], [1.01],
    [p_zero], [0.002], [0.001], [0.000], [0.004], [2660.0], [1.00],
    [rho], [0.959], [0.055], [0.861], [1.000], [1224.0], [1.00],
    [sigma], [2.164], [0.033], [2.098], [2.223], [3026.0], [1.00],
    [sigma_X[ln_population_density]], [0.125], [0.002], [0.121], [0.128], [2441.0], [1.00],
    [sigma_X[ln_gdp_pc]], [0.338], [0.005], [0.327], [0.347], [2674.0], [1.00],
    [sigma_X[precip_deviation]], [1.258], [0.029], [1.205], [1.312], [3285.0], [1.00],
    [sigma_X[co2]], [1.259], [0.029], [1.208], [1.314], [3362.0], [1.00],
    [sigma_X[population]], [0.126], [0.002], [0.123], [0.130], [2733.0], [1.00],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Summary Statistics of Model Parameters],
    note: []
  ),
  kind: table,
)
