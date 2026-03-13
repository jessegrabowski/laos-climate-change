#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 7pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (7fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    rows: (auto, 2pt, ) + (auto, ) * 17,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: .5pt + gray,
    hlinex(stroke: black + 3pt),
    [Parameter], [Mean], [SD], [HDI 3%], [HDI 97%], [MCSE Mean], [MCSE SD], [ESS Bulk], [ESS Tail], [R-hat],
    hlinex(stroke: black + 0.5pt),
    colspanx(10)[],
    hlinex(stroke: black + 0.5pt),
    [beta_log_distance_to_river_standardized], [-0.495], [0.091], [-0.664], [-0.317], [0.001], [0.001], [5004.0], [3724.0], [1.00],

    [beta_log_distance_to_coastline_standardized], [-0.489], [0.092], [-0.660], [-0.320], [0.001], [0.001], [4310.0], [4183.0], [1.00],

    [beta_Population_standardized], [-0.023], [0.098], [-0.207], [0.162], [0.001], [0.001], [7223.0], [4565.0], [1.00],
    [betaco2_standardized], [-0.462], [0.082], [-0.609], [-0.301], [0.001], [0.001], [5881.0], [4352.0], [1.00],

    [beta_precip_deviation_standardized], [0.210], [0.083], [0.056], [0.371], [0.001], [0.001], [7939.0], [4568.0], [1.00],

    [beta_dev_ocean_temp_standardized], [0.206], [0.065], [0.086], [0.331], [0.001], [0.001], [8230.0], [4351.0], [1.00],

    [beta_log_population_density_standardized], [-0.014], [0.099], [-0.203], [0.169], [0.001], [0.001], [5855.0], [4144.0], [1.00],

    [beta_log_gdp_per_cap_standardized], [-0.105], [0.099], [-0.288], [0.082], [0.001], [0.001], [7607.0], [4289.0], [1.00],

    [beta_log_gdp_per_cap_standardized_squared], [0.073], [0.077], [-0.070], [0.216], [0.001], [0.001], [6941.0], [4127.0], [1.00],

    [beta_log_population_density_standardized_squared], [-0.048], [0.095], [-0.226], [0.130], [0.001], [0.001], [5766.0], [4403.0], [1.00],

    [beta_log_distance_to_river_standardized_squared], [0.787], [0.067], [0.663], [0.915], [0.001], [0.001], [4169.0], [3879.0], [1.00],

    [beta_log_distance_to_coastline_standardized_squared], [0.591], [0.064], [0.474], [0.711], [0.001], [0.001], [3288.0], [3148.0], [1.00],

    [eta], [5.758], [1.580], [3.189], [8.636], [0.084], [0.059], [363.0], [728.0], [1.01],

    [eta_log], [1.716], [0.260], [1.239], [2.198], [0.014], [0.010], [363.0], [728.0], [1.01],

    [country_effect_THA], [0.111], [0.700], [-1.142], [1.459], [0.018], [0.013], [1473.0], [2123.0], [1.00],

    [country_effect_VNM], [-0.882], [0.737], [-2.238], [0.501], [0.017], [0.012], [1955.0], [2480.0], [1.00],

    [country_effect_KHM], [-0.010], [0.735], [-1.401], [1.338], [0.012], [0.010], [3781.0], [3947.0], [1.00],

    [country_effect_LAO], [-1.030], [0.680], [-2.304], [0.212], [0.012], [0.009], [3172.0], [3731.0], [1.00],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Statistical Summary of Parameters],
    note: [This table presents the statistical summary of for the estimated parameters for the event probability model full version model]
  ),
  kind: table,
)<full_events_sum>
