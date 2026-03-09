#import "../shared_functions.typ": title_and_note

= Modeling approach

== General approach

We focus on _natural disasters_ as key channel of impact of the climate on the economy.  We consider this to be a particularly relevant research  problem as:

#linebreak()

#set enum(indent: 25pt)
1. Climate researchers widely agree that disasters will likely become more frequent and more severe as the result of climate change.
2. Quantification of damages from discrete incidents of natural disaster is a tractable problem.
3. Specific actions related to disaster preparedness and prevention can be recommended to policy makers.

#linebreak()

Our objective is to quantify countries' exposure risk to disaster events. In particular, we focus on what #cite(<lopez_climate_2015>, form: "prose") define as hydrometeorological disasters, which comprises storms, floods, and movements of wet masses. The same methodology can, however, be applied to climatological disasters, which include droughts and, wildfires. Even when both disaster categories are deeply interconnected with climate dynamics, both require a separate treatment, as their causal relationships with precipitation differ significantly.

For the estimations we use a Bayesian modeling approach implemented through PyMC @abril2023pymc, a probabilistic programming language implemented in Python. This probabilistic approach offers us three crucial advantages:

#set list(indent: 15pt)
- First, the Bayesian framework facilitates the use of flexible Likelihood functions that more accurately represent the stochastic nature of disasters. Unlike traditional frequentist approaches—which often rely on asymptotic normality for inference or specific error-term assumptions (such as Gauss-Markov assumptions in OLS)—Bayesian modeling allows us to explicitly define non-normal generative processes. This is particularly relevant for disaster data, such as frequency and damage costs, which typically follow heavy-tailed or skewed distributions (e.g., Gumbel or Power Law) that are poorly captured by standard linear frameworks.

- Second, it allows us to estimate the entire probability distributions for events frequency and expected damages instead of just the expected values. This is extremely important, as this allows us to study the tails of the probability distributions where some of the most impactful events are located. By this approach we are able to quantify country exposure to different magnitudes of disasters.

- Third, it allows us to propagate uncertainty from one piece of the model to the other. This means that rather than treating intermediate estimates (such as disaster frequencies or economic vulnerabilities) as fixed inputs, we incorporate their full uncertainty into the final output. As a result, our estimates of exposure risk more accurately reflect the real-world ambiguity and variability inherent in climate-related data.

The modeling approach consists of seven components, illustrated in @modeling_approach. We present here a brief description of each section, however in further sections we will develop in detail each of the steps.

#figure(image("../images/modeling_approach.png", width:110%),
caption: title_and_note(
  title:[Modeling approach],
  ))<modeling_approach>

*1. Modeling disasters frequency*:

First, we use global data on disasters, climate and development indicators to model disaster frequency and predict the probability distribution of the number of disasters each country will face per year.

*2. Modeling expected disasters  damage*

We use the same global data on disasters, climate, and development indicators to model the probability distribution of the expected damages for each country over time.

*3. Modeling geospatial patterns of disasters*

Here we take a more granular approach to model the geospatial patterns of disasters inside countries. For this we use country maps and geolocalized information of disasters, rivers, and coastlines. We combine this information with global climate time series and development indicators to compute the probability of a disaster happening for each specific point on a country map. To model the geospatial patterns, we use a Gaussian Process, a non-parametric modeling technique with great power and flexibility.

To overcome some limitations of the geospatial information available in EM-DAT data set, we build an automatized query that uses an large language model to map some of the disaster-location in formation from text to geospatial coordinates. We consider this to be a relevant contribution to the current methodology in the field.

In contrast to the first two models, which are estimated simultaneously using data from all countries with available observations, the geospatial component is estimated using data from a specific region only, and predictions are generated for a single target country. This approach is necessary due to the substantial computational resources required to estimate the model at a global scale. To illustrate the methodology, we present results for two countries: Laos and Costa Rica.

*4. Modeling patterns of climate and development indicators*

In order to assess countries' future exposure, we model the time series patterns of climate and atmospheric indicators, as well as country-level development indicators. We use Bayesian Exponential Smoothing (ETS) models with additive damped trends, estimated via Kalman filtering, to capture level and trend dynamics in the data. We use this information to build future projections of key model variables.

*5. Country-level damage curves*

By combining the (1.) modelled disaster frequency and (2.) expected disasters damage, we are can create country-level damage curves, that measure the expected damage the country will experience conditional on the expected number of disasters, and their probability distribution. These damage curve computations are expressed using the "return years" notion. Return years describe the average frequency at which a certain level of damage is expected to be met or exceeded. For example, a 100-RY event (or simply a “100-year” event) corresponds to a damage level that has a 1% chance of being surpassed in any given year, or in other words, an event of such magnitude that is expected to happen on average once every 100 years.


*6. Geolocated damage curves*

Combining these country level damage curves (5) and the geospatial projection of the probability of a disaster (3), we build geolocalized damage curves, which measure the exposure of every point on a map to disasters.

*7. Assessing future exposure to climate change related disasters at national and local level*

Finally, we combine all the previous outputs to build projections of event frequency, damages, geospatial patterns of diaster occurrence, and country-level damage curves, as well as geolocalized damage curves.


== Underlying Causal Assumptions

To reason about our casual assumptions, we employ a causal model à la #cite(<pearl2009causality>, form: "prose"). @causal_graph shows the causal assumptions underlying our approach. "Economic Activity" and "Climate", as complex, abstract systems, are unobserved processes. Instead, we observe proxies for these: the GDP or population growth (in the case of the economy), or climatic indictors like atmospheric CO#sub[2] or ocean temperatures (in the case of the climate). The climate, together with the location of a specific place, determine the frequency and intensity of disasters. Economic activity also contributes to disaster severity. This occurs when resources are being deployed towards adaptation and resilience (e.g. with dykes, levees, and floodwalls), or when overexploitation creates new risks (such as mudslides resulting from overdevelopment). More economic activity and higher GDP also imply more potential for damages, either from destruction of expensive infrastructure or from interruptions to economic activity. Of course, we don't actually observe the true frequency ($f_P (p)$) or severity ($f_D (d)$) variables; these we are left to infer by observing the disasters that do occur.

#figure(image("../images/causal_graph.png", width:120%),
caption: title_and_note(
  title:[Causal Graph Between Economic Activity, Climate, and Disasters],
  note:[Dotted circles represent unobserved variables. Arrows connect concepts causally, so that $A -> B$ implies that $A$ causes $B$.],
  short_title:[Causal Graph Underlying our Approach]))<causal_graph>



The causal line between economic activity and disaster severity has a more quotidian interpretation, related to our definition of "severity". That is, we adopt an economic definition, wherein the severity of a disaster is measured by the cost of the damage it inflicts. As such, there must first be things to damage as a necessary precondition. The more things that exist, the more things that can be destroyed, and the greater potential for disaster impact.

Importantly, @causal_graph is silent on the specific functional relationships between variables. Each arrow on this diagram represents an entire discipline of study as shown in the literature review. Our objective is not to model these casual linkages individually, but to model them jointly.
