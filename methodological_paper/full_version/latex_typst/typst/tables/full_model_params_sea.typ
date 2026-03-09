#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note
#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (3fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    rows: (auto, 2pt, ) + (auto, ) * 11,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [Parameter], [mean], [sd], [ess_bulk], [ess_tail], [r_hat],
    hlinex(stroke: black + 0.5pt),
    [], [], [], [], [], [],
    [ell_log__[0]], [-1.37], [0.25], [3987.00], [4003.00], [1.00],
    [ell_log__[1]], [-1.35], [0.18], [4197.00], [4835.00], [1.00],
    [eta], [3.12], [0.36], [2088.00], [3751.00], [1.00],
    [eta_log__], [1.13], [0.11], [2088.00], [3751.00], [1.00],
    [beta[log_distance_to_river__standardized]], [-0.44], [0.03], [11561.00], [5363.00], [1.00],
    [beta[log_distance_to_coastline__standardized]], [-0.17], [0.06], [7776.00], [5073.00], [1.00],
    [beta[Population__standardized]], [0.10], [0.09], [14518.00], [6600.00], [1.00],
    [beta[co2__standardized]], [0.25], [0.06], [13074.00], [6135.00], [1.00],
    [beta[precip_deviation__standardized]], [0.33], [0.03], [8833.00], [5334.00], [1.00],
    [beta[dev_ocean_temp__standardized]], [0.02], [0.03], [8344.00], [4750.00], [1.00],
    [beta[log_population_density__standardized]], [0.32], [0.09], [14313.00], [6382.00], [1.00],
    [beta[log_gdp_per_cap__standardized]], [0.12], [0.08], [15245.00], [6216.00], [1.00],
    [country_effect[KHM]], [-1.75], [0.41], [5900.00], [5188.00], [1.00],
    [country_effect[LAO]], [-1.73], [0.43], [7930.00], [6514.00], [1.00],
    [country_effect[THA]], [-4.52], [0.26], [6296.00], [5787.00], [1.00],
    [country_effect[VNM]], [-3.87], [0.30], [5890.00], [5449.00], [1.00],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Summary Statistics of Model Full Model Parameters for Cambodia, Thailand, Laos and Vietnam],
    note: []
  ),
  kind: table,
)
