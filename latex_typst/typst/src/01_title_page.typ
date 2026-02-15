#import "../shared_functions.typ": title, authors, codes, keywords

#let abstract = lorem(100)


#set par(justify: false)
#text(size:36pt,
     fill:rgb("#4472C4"),
     weight:750,
     title)

#let count = authors.len()
#let ncols = calc.min(count, 3)

#set align(right)
#set par(leading: 7pt)

#grid(columns: (1fr,),
    row-gutter: 24pt,
    ..authors.map(author => [
        #author.name #author.extra \
        #author.affiliation \
        #link("mailto:" + author.email)
      ]),
    )

#set align(left)
#par(justify: true)[*Abstract*]

#set par(justify: true, first-line-indent: 0em)
#text("This paper develops a methodology to quantify countries’ exposure to climate change–related disasters, focusing on hydrometeorological events such as floods and storms. We introduce the Probabilistic Geospatial Risk (PGR) model, a fully Bayesian, multi-level system integrating time series, frequency, damage, and spatial sub-models. The framework captures uncertainty across the entire distribution of disaster frequency and damages, enabling robust estimation of both mean and tail risks. Using data from the EM-DAT disaster database, the World Bank, GPCC, and NOAA, we estimate disaster probabilities and damage distributions as functions of climate and development indicators. We further apply a Hilbert Space Gaussian Process (HSGP) to model fine-grained geospatial patterns of disaster occurrence within countries, complemented by state-space projections of climate and economic covariates. The model is demonstrated through two case studies—Costa Rica and the Lao People’s Democratic Republic. The resulting geolocalized damage curves and return-year estimates provide a transparent, reproducible tool for assessing future exposure to climate-related risks. This probabilistic approach advances the literature by integrating uncertainty quantification, geospatial modeling, and economic impact estimation into a coherent framework suitable for policy analysis and climate adaptation planning.")

#par(justify: false, first-line-indent: 0em)[
    *JEL Classification*: #codes.join(", ", last: ", and ")
  ]

#par(justify: false, first-line-indent: 0em)[
    *Keywords*: #keywords.join(", ")
  ]

#pagebreak()
