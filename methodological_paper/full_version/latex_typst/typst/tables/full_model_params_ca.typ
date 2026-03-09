#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note
#set text(size: 8pt)
#set par(justify: false)
#figure(
  tablex(
    columns: (3fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    rows: (auto, 2pt, ) + (auto, ) * 16,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: 0.5pt + gray,
    hlinex(stroke: black + 3pt),
    [Parameter], [mean], [sd], [ess_bulk], [ess_tail], [r_hat],
    hlinex(stroke: black + 0.5pt),
    [], [], [], [], [], [],
    [ell_log__[0]], [-0.48], [0.12], [4541.00], [5254.00], [1.00],
    [ell_log__[1]], [-0.22], [0.14], [3912.00], [5530.00], [1.00],
    [eta], [3.34], [0.43], [3177.00], [4311.00], [1.00],
    [eta_log__], [1.20], [0.13], [3177.00], [4311.00], [1.00],
    [beta[log_distance_to_river__standardized]], [-0.25], [0.05], [10393.00], [6385.00], [1.00],
    [beta[log_distance_to_coastline__standardized]], [0.02], [0.06], [10822.00], [6151.00], [1.00],
    [beta[Population__standardized]], [0.25], [0.08], [10462.00], [6294.00], [1.00],
    [beta[co2__standardized]], [0.44], [0.05], [10143.00], [6889.00], [1.00],
    [beta[precip_deviation__standardized]], [0.45], [0.03], [9750.00], [5208.00], [1.00],
    [beta[dev_ocean_temp__standardized]], [-0.19], [0.04], [9240.00], [5748.00], [1.00],
    [beta[log_population_density__standardized]], [0.27], [0.09], [11022.00], [6220.00], [1.00],
    [beta[log_gdp_per_cap__standardized]], [0.08], [0.09], [11172.00], [6233.00], [1.00],
    [country_effect[CRI]], [-1.30], [0.64], [5644.00], [5761.00], [1.00],
    [country_effect[GTM]], [-1.80], [0.68], [5179.00], [5044.00], [1.00],
    [country_effect[HND]], [-0.05], [0.59], [5167.00], [5114.00], [1.00],
    [country_effect[NIC]], [-0.53], [0.62], [5291.00], [5985.00], [1.00],
    [country_effect[PAN]], [-0.91], [0.69], [5392.00], [5844.00], [1.00],
    [country_effect[SLV]], [-1.68], [0.67], [6221.00], [6578.00], [1.00],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Summary Statistics of Model Full Model Parameters for Central America],
    note: []
  ),
  kind: table,
)
