#import "../shared_functions.typ": title_and_note




= Results


As a first step we present the results of the time series models for both countries. These results are extremely important as they allow us to project the covariates of the other models into the future, which is a requisite to produce predictions of the model results in the years to come.

== Time series model results

The goal of the time series model is to generate predictions for the covariates used in the disaster frequency, disaster damages, and geospatial patterns models. This allows us to project the models into the future and evaluate the impact of different CO₂ scenarios on country-level damage curves. First, we present the results for the global-level time series of CO₂ and ocean temperature, along with the deviation of ocean temperature from its trend. We observe that both atmospheric CO₂ and ocean temperature are projected to continue their upward trends, though the growth rate of ocean temperature is expected to smooth over time.

#figure(image("../images/results/time_series_pred_atmospheric_cols.png", width:110%),
caption: title_and_note(
  title:[Time series predictions for the global-level covariates],
  note: [CO2 is measured in Gigatones, ocean temperature is measured in fahrenheit  degrees, and ocean temperature deviation from its mean is measured in standard deviation units]))<global_time_series>

In the case of CO₂ emissions, we are interested in contrasting our projections with those developed by the IPCC (Intergovernmental Panel on Climate Change). The IPCC created several Special Report on Emissions Scenarios (SRES) @ipcc to model possible future climate conditions based on different socioeconomic pathways. Among these, A2 and B1 represent contrasting scenarios of global development and CO₂ emissions. Scenario A2 describes a high CO₂ emissions trajectory, often considered conservative in its assumptions, while scenario B1 represents an optimistic low CO₂ emissions pathway. Figure Table 8 shows the comparison between these two scenarios.

#include "../tables/co2_ipcc_scenarios.typ"

@co2_projections compares the trajectory of IPCC scenarios A2 and B1 with our own projections. We observe that scenario B1 aligns relatively closely with what our time series model projects, while scenario A2 shows a significant divergence. Our focus is on understanding how different CO₂ trajectories might impact the damage curves for the countries analyzed. To address this question, we will model the damage curves using both scenario A2 and our own projections.


#figure(image("../images/results/ipcc_co2_pred.png", width:100%),
caption: title_and_note(
  title:[IPCC and own projections of atmospheric ],
  note: [CO2 is measured in Gigatones, while ocean temperature is measured in Fahrenheit degrees. The deviation of ocean temperature from its trend value is measured in standard deviations.]))<co2_projections>


Regarding the country-level variables @cr_time_series and @lao_time_series present the projections for Costa Rica and Laos, respectively. In both cases, we observe an upward trend in GDP and population. For Costa Rica, the GDP growth rate surpasses the population growth rate, resulting in a rising GDP per capita. In contrast, for Laos, the projected population growth rate exceeds the GDP growth rate during a certain period, leading to a decline in GDP per capita. In the case of precipitation, the time series for both countries stabilize after following the current trend for a few years.

#figure(image("../images/results/time_series_pred_cr.png", width:110%),
caption: title_and_note(
  title:[Time series predictions for Costa Rica country level variables],
  note: [Population is measured in millions, real GDP in millions of USD, and precipitation is the whole monthly mean in millimeters.]))<cr_time_series>

#figure(image("../images/results/time_series_pred_lao.png", width:110%),
caption: title_and_note(
  title:[Population is measured in millions, real GDP in millions of USD, and precipitation is the whole monthly mean in millimeters.],
  note: []))<lao_time_series>


== Disaster frequency model

The sampling statistics of the frequency model are presented on tables 8 and 9. The sampling was implemented without divergences. The r_hat values for the results show a healthy samplong process. According to the Gelman–Rubin convergence diagnostic, the values of 1.00 mean that MCMC chains have converged to the same target posterior distribution. The only exception is the case oF beta_GY, which has some r_hat values above 1.00. In general, the ess_tal, which measures the effective sample size in the tails of the posterior distribution, reveal that we have reasonable sampling sizes, with the lowest one being 945.

#include "../tables/event_frequency_results_1.typ"

#include "../tables/event_frequency_results_2.typ"

@event_freq_res_lao presents the model results for Lao. Here the blue line provides the mean in-sample prediction, while the shaded region corresponds to the 95% High-Density-Interval (the darker the shade, the darker the probability for that value). We can see how the model succeeds to capture the general trend of the event's frequency, and how almost the observed number of events lie inside the 95% HDI values. In general, Loa presents a mean yearly number of events lower than one, with a trend to grow during the last decade, where the mean number of events increases up to one.

#figure(image("../images/results/result_event_freq_lao.png", width:110%),
caption: title_and_note(
  title:[Event Frequency model results for Lao],
  note: [Black points correspond to the observed numbers, blue line to the in-sample mean prediction, and shaded region to the 95% HDI, where lighter shadow reflects lower probability]))<event_freq_res_lao>


@event_freq_pred_lao reveal a clear upward trend in the number of yearly events, with the mean value increasing up to 3. The 95% Highest Density Interval (HDI) extends up to 6 events. This means that by 2020, we could be 95% confident that the number of hydrometeorological disasters in Laos was fewer than 3. By 2060, however, this number could increase to 6. (It is important to highlight that, for the purposes of this study, we are only considering events reported to affect more than 1,000 people).


#figure(image("../images/results/result_event_freq_pred_lao.png", width:110%),
caption: title_and_note(
  title:[Event Frequency model results for Lao],
  note: [Blue line to the mean prediction, and shaded region to the 95% HDI, where lighter shadow reflects lower probability]))<event_freq_pred_lao>


@event_freq_res_cr presents the model results for Costa Rica. The mean number of yearly disasters in the country starts around 0.5, with a growing trend that makes it approach to one. It is worth noting that in 2008 Costa Rica registered 4 events in one single year. In general we observe that the 95% High Density Interval manages to capture all the yearly values.


#figure(image("../images/results/result_event_freq_cri.png", width:110%),
caption: title_and_note(
  title:[ Event Frequency predictions for Costa Rica],
  note:[Black points correspond to the observed numbers, blue line to the in-sample mean prediction, and shaded region to the 95% HDI] ))<event_freq_res_cr>


@event_freq_res_pred_cr presents the projected trends. Just like in the case of Laos, we observe a growing trend, nevertheless in the case of Costa Rica, with the mean value reaching 2.5 in 2060, and the upper band of the 95% HDI growing up to 6 yearly disasters.

#figure(image("../images/results/result_event_freq_pred_cr.png", width:110%),
caption: title_and_note(
  title:[ Event Frequency predictions for Costa Rica],
  note:[Black points correspond to the observed numbers, blue line to the in-sample mean prediction, and shaded region to the 95% HDI] ))<event_freq_res_pred_cr>


We can conclude then than both countries are exposed to an increase of the number of hydrometeorological events in the years to come according to our model.

== Damages model

The sampling results for the damage model are presented on table 10, while the in sample model predictions are presented on @results_damages_lao and @results_damages_cr. The model was successfully sampled without divergences. From table 10 it is possible to observe that almost all al variables have a r_hat of 1.00 which reveals a healthy posterior approximation. However three particular variables have r_hat values greater to 1.01: alpha_X[ln_population_density, alpha_X[ln_gdp_pc, and beta_GX[ln_population_density. This reveals the MCMC had some conversion troubles for those particular variables. However, all the variables remain under the 1.05 threshold.

The effective sample sizes (ess_tail) are generally high, indicating that the MCMC chains have mixed well and that the posterior distributions are well-characterized. The variables alpha_X[ln_population_density, alpha_X[ln_gdp_pc, and beta_GX[ln_population_density present the lowest ess_tails, however the values are all equal or greater to 280, which still represent a reasonable size for posterior drawing.

#include "../tables/damage_results.typ"

The damage model results and predictions for Lao are presented in @results_damages_lao. This plot shows the in-sample damage predictions conditional on the occurrence of a disaster. We can observe how the country has experienced in the last decade three disasters that surpass in terms of damage all previous disasters. In that regard the 2018 flood was particularly destructive, with damages outside the 80% HDI. Interestingly, all the reported events are contained in the 95% HDI, with only two events outside the 80% HDI.

In terms of the projected values, the model does not project a growing trend int terms of the projected damages. Here it is important to take in consideration that the model has country-level hierarchy for different parameter, which means it infers different relations between covariates for countries.

#figure(image("../images/results/result_damages_lao.png", width:120%),
caption: title_and_note(
  title:[ Damage model results for Laos],
  note:[Red points correspond to the observed damages, light blue line corresponds to the 97.5% HDI, and wider blue line corresponds to 90% HDI. Damages are expressed in 2025 USD millions] ))<results_damages_lao>


Results for Costa Rica are presented in @results_damages_cr. All the registered events lie inside the 97.5% HDI. The two more destructive events correspond to the impact of Hurricane Cesar in 1996 and Hurricane Otto in 2017. Those are the only events outside the 80% HDI. In the case of the Central American country we do observe an increasing trend for the projected damages. With the upper band of the 97.5% of the High Density Interval increasing from 800 USD millions in 2020 to almost 1100 USD millions by 2060.

#figure(image("../images/results/result_damages_cr.png", width:120%),
caption: title_and_note(
  title:[ Damage model results for Costa Rica],
  note:[Red points correspond to the observed damages, light blue line corresponds to the 95% HDI, and wider blue line corresponds to 90% HDI. Damages are expressed in 2025 USD millions ] ))<results_damages_cr>

Therefore, our model predicts that Costa Rica will have a greater exposure to more impacfull events in the coming decades, while the projected mean damage of each event is not projected to increase in the case of Laos. Nevertheless, it is necesary to underscore that the total exposure is measured by the interaction of damages and frequency, which we will explore in the next section.

== Country level damages curve


To produce the damage curves, we combine the results of the damage and frequency models. @damage_curves_lao presents the damage curves for Laos. The vertical axis corresponds to damages in millions of USD, while the horizontal axis represents the probability associated with each damage level. As expected, most of the probability mass corresponds to low-damage events. However, as we consider less probable disasters, the magnitude of damages increases. The most relevant finding is that the model projects an upward shift in Laos’ damage curve, indicating that more impactful events will become more frequent, and more frequent events are projected to generate greater damages.

#figure(image("../images/results/damage_curves_lao.png", width:120%),
caption: title_and_note(
  title:[ Lao damage curves],
  note:[ ] ))<damage_curves_lao>


A more intuitive way of presenting the damage curves corresponds to the idea of *return years*. Table 12 and @damage_curves_cr present the projected year returns for Lao. The projected return year values illustrate a clear escalation of climate-related disaster risks for Laos over time. While the frequency of smaller-scale events (e.g., 2-year and 1-year returns) remains negligible, the table shows a marked increase in damages for rarer, high-impact events. For instance, the 100-year return value rises from approximately USD 611 million in 2000 to over USD 2.1 billion by 2055. Similarly, the 50-year return value more than triples within the same period. This pattern underscores how the severity of extreme events is expected to intensify, placing growing economic and social pressure on the country.

Importantly, the results also suggest that moderate return periods (10-year and 4-year events) will increasingly contribute to the overall risk landscape. By 2055, a 10-year return event is projected to cause damages exceeding USD 117 million, compared to just USD 23 million in 2000. This shift means that not only will catastrophic events become more damaging, but recurrent disasters will also impose higher recurring costs.

#include "../tables/return_years_lao.typ"




#figure(image("../images/results/damagecurves_barplots_lao.png", width:120%),
caption: title_and_note(
  title:[ Lao damage barplots],
  note:[ ] ))<damage_barplots_lao>

@damage_curves_cr presents the results for Costa Rica. In this case, we observe an even more pronounced increase in projected exposure to climate change–related disasters. In 2000, the probability of a disaster causing damages of USD 1,000 million was below 1%; however, by 2055, that probability is projected to rise to nearly 5%.

#figure(image("../images/results/damage_curves_cr.png", width:120%),
caption: title_and_note(
  title:[ CR damage curves],
  note:[ ] ))<damage_curves_cr>

Table 13 and @damage_barplots_cr present the return-year translations of the damage curves for Costa Rica. The projected return year values reveal a steep rise in expected damages from hydrometeorological disasters over the coming decades for the Central American nation. For rare but extreme events, the increase is particularly dramatic: the 100-year return value grows from about USD 1.2 billion in 2000 to more than USD 6.5 billion by 2055. Likewise, the 50-year return damages more than quadruple over the same period. This upward trend highlights how climate change is projected to significantly amplify the economic impacts of extreme disasters.

The data also show that damages from more frequent events are rising sharply, underscoring the increasing cost of recurrent disasters. For example, a 10-year return event is projected to escalate from about USD 32 million in 2000 to over USD 400 million by 2055, while 4-year return events—once negligible—are expected to reach nearly USD 47 million by mid-century. This shift suggests that climate change will not only increase the burden of catastrophic losses but also impose growing, recurring costs on communities and infrastructure.

#include "../tables/return_years_cr.typ"


#figure(image("../images/results/damagecurves_barplots_cr.png", width:120%),
caption: title_and_note(
  title:[ CR damage barplots],
  note:[ ] ))<damage_barplots_cr>

== Geospatial patterns model
=== HSGP modeling

First, we implement a simplified geospatial model that relies solely on an HSGP component to estimate the probability of a disaster occurring at any given point within a country. This simplified HSGP version uses only latitude and longitude as independent variables, making it time-independent.

The results, shown in @hsgp_sea, cover Cambodia, Thailand, Laos, and Vietnam. It is striking to see how the model can infer the outlines of major rivers purely from disaster occurrence patterns. We also observe that certain coastal regions exhibit greater exposure to disasters. This reinforces the idea that the HSGP component of the model represents a strong tool to account for omitted variables, as it is able to capture patterns of geographical patterns not explicitly included in the model. These results also  confirm the notion that distance to rivers and coastlines represent a clear risk factor in the region.

HSGP parameter values for  Cambodia, Thailand, Laos and Vietnam, and HSGP parameter values for Central America can be found on Tables 16 and 17 of Annex 2 respectively.

#figure(image("../images/results/event_HSGP_sea_pred.png", width:100%),
caption: title_and_note(
  title:[ HSGP event probability predictions for Cambodia, Thailand, Laos and Vietnam],
  note:[The plot value measures the yearly probability that a disaster will happen on each specific point conditional on the occurrence of one disaster] ))<hsgp_sea>

@hsgp_lao presents the results specifically for Lao. Based only on the coordinates of previous disasters, the model is able to identify a risk zone in the center-left area of the country, precisely where a big number of rivers merge. It also identifies a risk area closer to the capital Vientiane, and in two more points in the lower right area of the country.


#figure(image("../images/results/event_HSGP_lao_pred.png", width:100%),
caption: title_and_note(
  title:[ HSGP event probability predictions for Lao],
  note:[The plot value measures the yearly probability that a disaster will happen on each specific point conditional on the occurrence of one disaster] ))<hsgp_lao>


The results for Central America are presented on @hsgp_ca. It is possible to observe how the model successfully captures the disaster patterns.
  #figure(image("../images/results/hsgp_central_america.png", width:120%),
caption: title_and_note(
  title:[ HSGP event probability predictions for Central America],
  note:[The plot value measures the yearly probability that a disaster will happen on each specific point conditional on the occurrence of one disaster] ))<hsgp_ca>

The results for Costa Rica, presented in @hsgp_cr, show a different pattern from those observed in Laos. The HSGP locates most of the risk in the central region of the country, known as the Greater Metropolitan Area, which is home to the majority of the population. It also indicates elevated risk in Guanacaste, particularly around Liberia, another major population center. Finally, the HSGP component estimates considerable risk along the Caribbean coast near the border with Panama, a region well known for its susceptibility to floods.

  #figure(image("../images/results/hsgp_cr.png", width:90%),
caption: title_and_note(
  title:[ HSGP event probability predictions for Costa Rica],
  note:[The plot value measures the yearly probability that a disaster will happen on each specific point conditional on the occurrence of one disaster] ))<hsgp_cr>


=== Full model

Now, we present the estimated results for the full model, starting with Laos and its neighboring countries. It is important to highlight that we choose Lao, Costa Rica and their neighboring countries as examples, nevertheless, the model can generate estimations and results for almost any country or region in the world for which the data is available.

For an easier understanding, we present the results in maps, however, the model produces specific probabilities for each point of the country, which can be used for specific computations. We will present an example of this later


Tables 18 and 19 on Annex 2 contain the main parameter values of both Full Model estimations. @results_sea_full shows the results for Cambodia, Thailand, Laos, and Vietnam. It is possible to observe that the distance to rivers is a relevant determinant of exposure to hydrometeorological events. However, it is not just the distance to any river that matters—the model combines the geospatial patterns identified by the HSGP with river distance information to determine high-risk areas. Consequently, some areas have a relatively low probability of events despite being close to rivers.

The same is true for distance to the coastline. The model is able to determine which coastal regions pose the greatest risk, as can be seen in the eastern part of the region. As mentioned earlier, this is due to the capacity of the HSGP component to identify and project geospatial patterns, which helps account for missing covariates.
  #figure(image("../images/results/full_model_sea_2018.png", width:90%),
caption: title_and_note(
  title:[ Full model event probability predictions for Cambodia, Thailand, Laos and Vietnam],
  note:[The plot value measures the yearly probability that a disaster will happen on each specific point conditional on the occurrence of at least one disaster] ))<results_sea_full>


We now zoom in to examine in more detail the specific results for Laos. @results_lao_full presents the results for the country. Once again, we can see how the model is able to identify which rivers represent greater risks according to the geospatial patterns of past disasters.

#figure(image("../images/results/full_model_lao_2018.png", width:90%),
caption: title_and_note(
  title:[ Full model event probability predictions for Lao],
  note:[The plot value measures the yearly probability that a disaster will happen on each specific point conditional on the occurrence of at least one disaster] ))<results_lao_full>


@decomposed_result_lao present the decomposition of the effects for Lao. It is important to consider that besides the effects plotted, the event probability risk is also affected by the country effect, the climate covariates and the country-level covariates, which do not vary at the geospatial level. The decomposition of the effects allows to identify that the HSGP component dominates the projected probability values. It also shows that despite having a lower weight, the distance to coastline has some positive impact, as can be seen in the lower right segment.

#figure(image("../images/results/decomposed_effect_lao.png", width:100%),
caption: title_and_note(
  title:[Decomposition of the full model event probability predictions for Lao ],
  note:[] ))<decomposed_result_lao>

The static geospatial perspective is highly valuable in itself; nevertheless, we are interested in understanding how exposure to climate change risks evolves over time and how it is affected by projected climate trends. To do this, we multiply the geospatial event probability by the mean number of events the country is projected to experience per year. This provides the total event probability per year for each point. We then project these values over time to understand how risk evolves as atmospheric CO₂ increases. @results_lao_yearly shows how local exposure increases over time for Laos.

#figure(image("../images/results/full_model_yearly_lao.png", width:120%),
caption: title_and_note(
  title:[ Full model event probability predictions for Lao trough time],
  note:[] ))<results_lao_yearly>



We now present the results for Central America and Costa Rica. @results_ca_full shows the results for the whole region, while @results_ca_full present the estimations specifically for Costa Rica. In the case of Costa Rica, we observe how the riskiest areas seem to be concentrated in the great metropolitan area, which contains most of the country's population.


  #figure(image("../images/results/full_model_ca_2018.png", width:90%),
caption: title_and_note(
  title:[ Full model event probability predictions for Central America],
  note:[The plot value measures the yearly probability that a disaster will happen on each specific point conditional on the occurrence of at least one disaster] ))<results_ca_full>

#v(-25pt)
  #figure(image("../images/results/full_model_cr_2018.png", width:80%),
caption: title_and_note(
  title:[ Full model event probability predictions for Costa Rica],
  note:[The plot value measures the yearly probability that a disaster will happen on each specific point conditional on the occurrence of at least one disaster] ))<results_cr_full>


@results_ca_full shows the decomposition of the effects. In the case of Costa Rica, we observe the particularity that distance to the coastline has a very limited influence on event probability, with shorter distances to the coastline leading to slight decreases in event probability. One possible explanation for this is the concentration of recorded disasters in more densely populated areas (such as the Greater Metropolitan Area in the center of the country), which results in a lower estimated probability along the coasts, where population density is much lower.

#figure(image("../images/results/decomposed_effect_cr.png", width:100%),
caption: title_and_note(
  title:[Decomposition of the full model event probability predictions for Costa Rica],
  note:[] ))<decomposed_result_cr>

To conclude this section, we present on @results_cr_yearly the projected geospatial risk for Costa Rica. Similar to the case of Lao, we can observe how the probability of event increases in the riskier areas as atmospheric CO2 projections growth trough time. The projections show a greater exposure for the Greater Metropolitan Area, Guanacaste and the south of the Caribbean.
  #figure(image("../images/results/full_model_yearly_cr.png", width:120%),
caption: title_and_note(
  title:[ Full model event probability predictions for Costa Rica],
  note:[] ))<results_cr_yearly>



== Geolocated return year curves

One of the main contributions of this paper is to provide local-level estimates of event probabilities and the expected damages caused by climate change–related disasters. This approach is not intended to replace on-site hydrological studies, but rather to offer a low-cost and efficient tool that can provide initial approximations of risk.

The model makes it possible to compute these values for any point within the analyzed country. To illustrate this, we focus on three specific locations in Costa Rica:
- Desamparados (San José)
- El Bambú (Filadelfia, Guanacaste)
- Cariari (Pococí, Limón)


These locations are shown in @locs_cr_map

#figure(image("../images/results/loc_cr_map.png", width:75%),
caption: title_and_note(
  title:[ Selected locations],
  note:[] ))<locs_cr_map>

Table 14 shows the yearly probability of an event happening on each point though time. We can observe that Desamparados presents the greater probability and Cariari the lowest one from the three points. Also it is possible to observe how the risk exposure increases for all the locations across time.

#include "../tables/location_prob_cr.typ"

We use the local probability to scale down the national expected damage, and produce a local level return year curves. These curves do not consider local characteristics of infrastructure, or physical capital, bu are local projections of the national damages using the local event probability (which does capture some of this patterns via the HSGP component).

This local projections allows us to quantify the climate change risk exposure at a granular level, and produce approximations of the impacts that particular communities can suffer due to climate change related disasters. To exemplify this, we present on @return_yeras_fila the return year curves for El Bambú (Filadelfia, Guanacaste), Consistent with what has been observed in the previous results, the return year curves reveal a growing pattern in terms of damage exposures as more severe events become more frequent, and more frequent events become more severe.

#figure(image("../images/results/filadelfia_return_years.png", width:100%),
caption: title_and_note(
  title:[ Geolocated projected return year curves for 'El Bambú (Filadelfia, Guanacaste)],
  note:[Estimated damages are measured in millions of 2025 USD ] ))<return_yeras_fila>
