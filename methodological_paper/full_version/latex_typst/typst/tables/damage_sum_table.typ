#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (3fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    rows: (auto, 2pt, ) + (auto, ) * 9,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: .5pt + gray,
    hlinex(stroke: black + 3pt),
    [Parameter], [Mean], [SD], [HDI 3%], [HDI 97%], [MCSE Mean], [MCSE SD], [ESS Bulk], [ESS Tail], [R-hat],
    hlinex(stroke: black + 0.5pt),
    colspanx(10)[],
    hlinex(stroke: black + 0.5pt),
    [betas-damage-Population-standardized], [0.291], [0.935], [-1.316], [1.333], [0.380], [0.283], [6.0], [10.0], [4.46],
    [betas-damage-log-population-density-standardized], [-0.304], [0.901], [-1.985], [0.939], [0.366], [0.273], [6.0], [11.0], [4.52],
    [betas-damage-log-gdp-per-cap-standardized], [-0.091], [0.843], [-1.379], [1.056], [0.343], [0.255], [6.0], [11.0], [4.62],
    [betas-damage-dev-ocean-temp-standardized], [-0.265], [1.070], [-1.489], [1.752], [0.435], [0.324], [6.0], [11.0], [4.91],
    [betas-damage-co2-standardized], [0.235], [1.022], [-1.843], [1.199], [0.415], [0.309], [6.0], [11.0], [4.90],
    [betas-damage-precip-deviation-standardized], [-0.083], [0.714], [-0.998], [0.852], [0.290], [0.216], [6.0], [12.0], [5.07],
    [betas-damage-log-gdp-per-cap-standardized-squared], [-0.583], [0.830], [-1.778], [0.849], [0.337], [0.251], [6.0], [11.0], [5.15],
    [sigma-damage], [1.701], [0.937], [0.477], [3.016], [0.381], [0.283], [7.0], [21.0], [3.82],
    [sigma-damage-log], [0.342], [0.654], [-0.741], [1.104], [0.266], [0.198], [7.0], [21.0], [4.21],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Statistical Summary of Damage Parameters],
    note: [This table presents the statistical summary of various damage parameters, including their mean, standard deviation (SD), highest density interval (HDI) at 3% and 97%, Monte Carlo standard error (MCSE) for mean and SD, effective sample size (ESS) for bulk and tail, and the potential scale reduction factor (R-hat).]
  ),
  kind: table,
)<damage_parameters_summary_modified>
