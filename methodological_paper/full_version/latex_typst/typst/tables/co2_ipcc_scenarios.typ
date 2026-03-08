
#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note

#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (1fr, 1.5fr, 1.5fr),
    rows: (auto, 2pt, ) + (auto, ) * 6,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: .5pt + gray,
    hlinex(stroke: black + 3pt),
    [Factor], [A2 (High Emissions)], [B1 (Low Emissions)],
    hlinex(stroke: black + 0.5pt),
    colspanx(3)[],
    hlinex(stroke: black + 0.5pt),
    [Economic Growth], [Regional, slower progress], [Global, sustainable],
    [Population], [~15 billion (high)], [~9 billion (stable)],
    [Energy], [Fossil fuel-dominated], [Renewable energy transition],
    [CO₂ Levels (2100)], [~850+ ppm], [~550 ppm],
    [Temperature Rise (2100)], [3.5 - 5.5°C], [1.5 - 2.5°C],
    [Climate Risks], [Severe heatwaves, storms, sea level rise], [Milder impacts, adaptation possible],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Comparison of IPCC Scenarios A2 and B1],
    note: [This table compares key factors between the high emissions (A2) and low emissions (B1) scenarios.]
  ),
  kind: table,
)<ipcc_scenarios_table>
