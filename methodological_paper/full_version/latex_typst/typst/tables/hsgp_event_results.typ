#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (2fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    rows: (auto, 2pt, ) + (auto, ) * 7,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: .5pt + gray,
    hlinex(stroke: black + 3pt),
    [Parameter], [Mean], [SD], [HDI 3%], [HDI 97%], [MCSE Mean], [MCSE SD], [ESS Bulk], [ESS Tail], [R-hat],
    hlinex(stroke: black + 0.5pt),
     colspanx(10)[],
    hlinex(stroke: black + 0.5pt),
    [ell_lat], [0.596], [0.055], [0.484], [0.690], [0.001], [0.001], [2997.0], [4207.0], [1.0],

    [ell_long], [0.504], [0.039], [0.432], [0.577], [0.001], [0.001], [2684.0], [4034.0], [1.0],

    [ell_log_0], [-0.522], [0.093], [-0.695], [-0.345], [0.002], [0.001], [2997.0], [4207.0], [1.0],
    [ell_log_1], [-0.688], [0.078], [-0.837], [-0.548], [0.001], [0.001], [2684.0], [4034.0], [1.0],
    [eta], [4.464], [0.314], [3.869], [5.043], [0.009], [0.006], [1364.0], [2609.0], [1.0],
    [eta_log], [1.494], [0.070], [1.366], [1.629], [0.002], [0.001], [1364.0], [2609.0], [1.0],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Statistical Summary of Parameters],
    note: [This table presents the statistical summary of for the estimated parameters for the event probability model with the HSGP component only.]
  ),
  kind: table,
)<hsgp_event_results>
