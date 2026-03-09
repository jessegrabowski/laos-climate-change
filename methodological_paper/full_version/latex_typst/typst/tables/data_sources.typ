#import "@preview/tablex:0.0.9": tablex, colspanx, hlinex
#import "../shared_functions.typ": title_and_note, OECD_blue

#set text(size: 8pt)
#set par(justify: false)

#figure(
  tablex(
    columns: (2.5fr, 1fr, 3fr),
    rows: (auto, 2pt, ) + (auto, ) * 7,
    align: left + horizon,
    auto-lines: false,
    inset: 5pt,
    stroke: .5pt + gray,
    map-rows: (row, cells) => cells.map(c =>
    if c == none {
        c  // keeping 'none' is important
    } else {
        (..c, fill: if row == 0 { OECD_blue } else if
        row > 2 and calc.rem(row, 2) == 1 { OECD_blue }
                else { white })
              }
    ),
    hlinex(stroke: black + 3pt),
    [*Title*], [*Source*], [*Summary*],
    hlinex(stroke: black + 0.5pt),
    [], [], [],
    hlinex(stroke: black + 0.5pt),
    [EMDAT International Disaster Database], [CRED], [Historical database recording disaster occurrences and impacts worldwide.],
    [NOAA Atmospheric $"CO"_2$ Dataset], [NOAA], [Detailed records of atmospheric carbon dioxide levels collected over time for climate research.],
    [NOAA Ocean Surface Temperature Dataset], [NOAA], [Historical measurements of ocean surface temperatures.],
    [Global Precipitation Climatology Centre Dataset], [GPCC], [Historical records of precipitation at various levels of geographic resolution.],
    [HydroSHEDS Global Hydrography Dataset], [WWF], [High-resolution geospatial data detailing river networks, along with flow data.],
    [World Development Indicators], [World Bank], [Economic, social, and environmental indicators],
    [World Bank Shapefiles of National Boundaries], [World Bank], [Maps of country and administrative borders.],
    hlinex(stroke: black + 3pt),
  ),
  caption: title_and_note(
    title: [Summary of Data Sources Used in our Modeling Pipeline],
    note: [Table provides a title and organizational source for each dataset. See the main text for detailed citations associated with each dataset.]
  ),
  kind: table,
)<data_table>
