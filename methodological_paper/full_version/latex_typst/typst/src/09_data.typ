#import "../shared_functions.typ": title_and_note

= Data

== Data sets summary

To process the data for the project, we built an open source automatized pipeline that downloads and process the data. The pipeline can be accessed in projects' repository  #link("https://github.com/jessegrabowski/laos-climate-change/tree/main/laos_gggi/data_functions")[
  *link*]. We want to make this data pipeline publicly available as an
  exercise of transparency, to facilitate replication and because we are engaged promoters of open-source software.


The data sets used to build the Probabilistic GeoRisk model can be classified into three different categories:


*1. Country-level information*

Following the approach of @lopez_climate_2015, we use the World Bank World Development Indicators @worldbank_wdi_2024, which contain a panel of yearly information for almost all countries in the world. From this data set, we extract each country's GDP per capita, population density, and total population.

To obtain each country's deviation from its trend precipitation, we use the GPCC world precipitation data set @gpcc_2022, which contains geospatial information all around the world. The data set provides the monthly total precipitation on a regular grid with a spatial resolution of 0.25° x0.25° , 0.5° x 0.5°, 1.0° x 1.0°, and 2.5° x 2.5° latitude by longitude. Using each country's shapefile, we transform this geospatial information into a country-level time series from which we calculate the trend and the deviation with respect to that trend.

We also use the EM-DAT data set @cred_emdat_2024 to obtain the total number of disasters per country and the economic damages they caused. As found by Botzen, Deschenes and Sanders @Botzen2019 other data sets like  NatCatSERVICE and Sigma provide detailed information about disasters, especially in terms of disaster geolocation. Nevertheless, we decided to use the EM-DAT database given its public availability, and its status as the academic standard.

When working with EM-DAT disasters register, it is important to take into account possible reporting biases, as disasters with less severe impacts may not have been registered. Additionally, it is possible that as the reporting capacities of countries increase, the rate of registration of these minor events changes. To address this, we include some initial filters by considering only disasters after 1980 that affected more than 1   000 people according to the reported impact. We also limit the analysis to hydrometeorological disasters, which comprise storms, floods, and movements of wet masses. By applying these filters, the number of disaster observations is reduced from 26 664 to 5 692.


*2. Global-level climate time series*

At the world time series level, we use NOAA's (National Oceanic and Atmospheric Administration) atmospheric CO2 concentration data set @noaa_co2_2024, which provides the worldwide levels of CO2 atmospheric concentration in Gigatons. We also obtain the world's mean ocean temperature and its deviation from trend from the NOAA's Global Surface Temperature Dataset @zhang_noaa_2019.



*3. Geospatial data sets*

In terms of geospatial information, we use the shapefiles from the World Bank Official Boundaries @worldbank_boundaries_2024, which contain the official maps of the territory and administrative divisions for each country. We also use the world river data set from HydroSEHDS @lehner_global_2013, which contains the maps of all the rivers around the world. We also use the geospatial coordinates for disasters contained in the EM-DAT data set @cred_emdat_2024, which provide the exact geographical zone affected by each event.

In terms of geospatial information EM-DAT data set has an important limitation, as most of the disasters are missing the coordinates data. Nevertheless, practically all of them have the exact name or names of the place where the disaster took place. To overcome this limitation, we developed an automatic query for an artificial intelligence model which transformed the location into exact coordinates. Details about this procedure are given in the current section.

#v(15pt)

#include "../tables/data_sources.typ"


== Event frequency data

For the event frequency data, we transform the EM-DAT dataset to obtain a count of the total number of disasters per country per year. To do this, we assume that for countries with no recorded disasters in a given year, the count is zero. We then merge this dataset with the World Bank Development Indicators (@worldbank_wdi_2024), the CO₂ data from @noaa_co2_2024, ocean temperature data from @zhang_noaa_2019, and the global precipitation dataset from @gpcc_2022.

As previously mentioned, the precipitation data is provided at a geospatial level. Therefore, we use the World Bank shapefiles to assign each point to its corresponding country. We then compute the average annual precipitation per country, along with its deviation from the long-term trend. For the ocean temperature data, we similarly compute deviations from the historical mean.

Table 2 presents summary statistics for the disaster event counts. In @event_k_den, we show the kernel density plot and histogram of these counts. As can be seen, there is a significant concentration around zero, indicating that in most countries, the number of reported hydrometeorological disasters per year is zero. This observation is relevant, as it justifies the use of a Zero-Inflated Binomial probability distribution to model event occurrence.

#v(15pt)

#include "../tables/event_sum.typ"


#figure(image("../images/eda/event_kden.png", width:60%),
caption: title_and_note(
  title:[Kernel density for yearly count of hydrometereological disasters by country],
  note:[ ],
  short_title:[Mean number of hydrometereological disasters per country]))<event_k_den>

In @event_trend, we show the historical mean across all countries for the number of hydrometeorological events reported per year. A clear upward trend is observed. This may be partly due to reporting bias: as countries improve their institutional capacity, the number of recorded disasters tends to increase. However, it is important to note that we have already applied a filter to mitigate this bias by including only disasters that affected more than 1,000 people and occurred after 1980.

It is important to highlight that the GPCC precipitation dataset is only available up to 2020. To address this limitation, we estimate the model using data from 1980 to 2020. For predictions in more recent years, we use actual observed data for all covariates except precipitation, for which we rely on forecasts generated by a time series model.

#figure(image("../images/eda/event_trend.png", width:70%),
caption: title_and_note(
  title:[Yearly mean across countries of the number of hydrometereological disasters],
  note:[ ],
  short_title:[Example Damage Curve]))<event_trend>

Table 3 and @event_kdensity_features present a general summary of the data used as covariates in the model.




#include "../tables/event_sum_2.typ"

#v(25pt)

#figure(image("../images/eda/event_features_kden.png", width:110%),
caption: title_and_note(
  title:[Kernel density for covariates included in the event frequency model],
  note:[ ],
  short_title:[Kernel density for covariates included in the event frequency model]))<event_kdensity_features>



== Disaster damage data

Table 4 presents the summary for the damages data used for the damages model. One important limitation is that the number disasters on the EM-DAT  data set for which there is a reported damage value is considerably lower. As a consequence, the number of observations for the damage model is less than half of those in the event one: 2 300 vs. 5 692.

EM-DAT data set provides the damage values adjusted to 2011 USD, we adjust them to 2025 using the consumer price index time series from the U.S. Bureau of Statistics @fred_cpi

#include "../tables/damages_sum.typ"


As seen in @damages_kden, the damages data is characterized for a extreme values reported in the biggest global economies like the United, China and Japan. One clear example of this is the damages reported for hurricane Katrina in 2005, which have a 2025 adjusted value of 262 USD billions.

#figure(image("../images/eda/damages_kden.png", width:90%),
caption: title_and_note(
  title:[Kernel density for yearly damages of hydrometereological disasters],
  note:[ ],
  short_title:[Kernel density for yearly damages of hydrometereological disasters]))<damages_kden>


In contrast with the number of events registered, the damages of hydrometereological disasters do not show a clear upward trend, as seen in @damage_trend. Data reveals a peak of damages reported in 2005, a year where a set of highly destructive events were reported worldwide, including hurricane Katrina.

#figure(image("../images/eda/damages_trend.png", width:90%),
caption: title_and_note(
  title:[Historical trend of yearly damages of hydrometereological disasters],
  note:[ ],
  short_title:[Historical trend of yearly damages of hydrometereological disasters]))<damage_trend>


Table 5 presents the descriptive statistics for the features used in the damage model. In this case, to reduce the computing capacity required to estimate and sample the model, we standardize the features by substracting the mean and dividing by the standard deviation.



#include "../tables/damages_sum_features.typ"


#figure(image("../images/eda/damage_features_kden.png", width:110%),
caption: title_and_note(
  title:[Kernel density for the covariates used in the damage model],
  note:[ ],
  short_title:[Kernel density of damage model covariates]))<damage_features_kden>

== geospatial data

The backbone of the geospatial analysis is given by the World Bank country shapefiles @worldbank_boundaries_2024. Using the shapefiles, we can match geospatial information like latitude and longitude, with country-level information.

*Use of Artificial Intelligence to complete locations*

The use of EM-DAT disaster data at the geospatial level faces a significant challenge: out of 5 692 hydrometeorological disasters for which we have information, only 864 have associated geospatial coordinates. In contrast, 5,640 observations include data in the "Location" field, which typically contains the names of the places affected by the event in text format. It is important to note that this field often includes multiple locations, as a single disaster can impact several areas simultaneously. The key challenge, therefore, is to convert this location information from text format into geospatial coordinates.

To address this, we developed an automated query system that sends the location information to a large language model—in this case, OpenAI’s GPT-4 mini (@openai2024gpt4omini)—and requests the corresponding geographic coordinates. We then apply a validation step to ensure that the returned coordinates fall within the correct country boundaries. After processing, we are able to transform the textual location data into 2,876 individual coordinate points associated with the recorded events. @gpt_query compares in a map the geospatial representation of disaster locations before and after the query.

#figure(image("../images/eda/gpt_query_comp.png", width:100%),
caption: title_and_note(
  title:[Disasters with coordinates before and after the AI query],
  ))<gpt_query>



@laos_year_map and  present the maps for Costa Rica and Lao with the exact location and year of the hydrometeorological disasters after the query done with Artificial Intelligence.




#figure(image("../images/eda/year_event_map_lao.png", width:65%),
caption: title_and_note(
  title:[Disaster geographical distribution by year for Lao],
  ))<laos_year_map>


#v(-35pt)


#figure(image("../images/eda/year_event_map_cr.png", width:77%),
caption: title_and_note(
  title:[Disaster geographical distribution by year for Costa Rica],
  ))<cr_year_map>


*River data set*

For the rivers, we use a similar approach. From the HydroSHEDS database @lehner_global_2013, we obtain the coordinates for all the rivers around the world. Using one criterion, we filter the rivers to have those with the greater probability of causing floods: we include only the rivers with a long-term average discharge greater than 100 m³. Which refers to rivers that have in the data set the ORD_FLOW variable smaller than 5. @rivers present the world mapping of the river data set used.


#figure(
  image("../images/eda/world_rivers.png" ,  width: 110%),
  caption: [
   World rivers with a long-term average discharge greater than 100 m3
  ],
) <rivers>

=== Local data sets for geospatial modeling

In contrast to the first two models, which are estimated simultaneously using data from all countries with available observations, the geospatial component is estimated using data from a specific region only, and predictions are generated for a single target country. This approach is necessary due to the substantial computational resources required to estimate the model at a global scale. To illustrate the methodology, we present results for two countries: Laos and Costa Rica.

To train the model for Laos, we use data from the next countries: Cambodia, Thailand, Laos and Vietnam. While for Costa Rica we use data from Costa Rica,  El Salvador,  Guatemala,  Honduras, Nicaragua and Panama.

*Generation of fake non disaster data points*

To estimate the geolocated probability of a disaster occurring at a specific point, we generate a set of synthetic non-disaster points and train a model to distinguish between real disaster locations and these synthetic counterparts. For each disaster point within a country, we randomly simulate 15 non-disaster points.

It is important to note that the disaster-to-non-disaster ratio does not affect the resulting probability values, as the outputs are normalized by dividing each by the sum of all point probabilities. However, through extensive testing, we found that a 1:15 ratio is particularly effective for generating high-quality samples for the HSGP model.

We then merge the disaster and synthetic non-disaster points into a single dataset. For each point, we calculate the distance to the nearest river and the nearest coastline. We also assign to each point the relevant country-level covariates for the year in which the event occurred and we standardize them to facilitate the estimation of the model. The full set of covariates used (all standardized by susbstracting the mean and scaling by the standard deviation) is:

- Log of distance to river.
- Log of distance to coastline.
- Population.
- Accumulated atmospheric CO2 in Gigatons.
- Country's precipitation deviation from its Trend.
- Ocean temperature deviation from its Trend.
- Log of population density.
- Log of population density squared.
- Log of GDP per capita.
- Log of GDP per capita squared.

@ca_dis and @laos_neigh_dis show the maps of disaster and synthetic non-disaster points for both regions. Since we generate 15 random non-disaster points for every disaster, the point density is lower in countries with fewer recorded disasters. It is important to note that this does not affect the model’s estimates related to event frequency, as that aspect is handled by the event component of the model, not in the geospatial component described here.

In the case of Costa Rica, we exclude Isla del Coco from the map and its surroundings to facilitate visualization.

#figure(image("../images/eda/ca_real_synth_dis.png", width:80%),
caption: title_and_note(
  title:[ Disaster and synthetic non-disaster points for Central America],
  note:[Yellow points correspond to reported disasters, purple to randomly generated non-disaster points ]))<ca_dis>

#v(-25pt)

#figure(image("../images/eda/laos_neigh_real_synth_dis.png", width:55%),
caption: title_and_note(
  title:[ Disaster and synthetic non-disaster points for Cambodia, Thailand, Laos and Vietnam],
  note:[Yellow points correspond to reported disasters, purple to randomly generated non-disaster points ]))<laos_neigh_dis>

We provide the descriptive statistics of the datasets used to train the model for Costa Rica and Laos in Tables 6 and 7, respectively. The histograms and kernel density plots are presented in @geo_features_kden_ca and @geo_features_kden_laos_neigh in Annex 1.

#include "../tables/geo_sum_ca.typ"

#include "../tables/geo_sum_laos_neigh.typ"


== Result grids.

To visualize the model results and evaluate the probability of a disaster happening on every point of Costa Rica and Laos, we project each contry's map to a 400 x 400 grid. Then for each point of the grid we compute the distance to the closest river, and the distance to the nearest coastline point, then we merge that grid data set with the country level indicators of the year to evaluate. We present the grids for both countries, and the plotting of the distance to rivers and coastline, in @cr_grid and @laos_grid

#figure(image("../images/eda/cr_grid.png", width:120%),
caption: title_and_note(
  title:[ Disaster and synthetic non-disaster points for Cambodia, Thailand, Laos and Vietnam],
  note:[Yellow points correspond to reported disasters, purple to randomly generated non-disaster points ],))<cr_grid>


#figure(image("../images/eda/laos_grid.png", width:120%),
caption: title_and_note(
  title:[ Disaster and synthetic non-disaster points for Cambodia, Thailand, Laos and Vietnam],
  note:[Yellow points correspond to reported disasters, purple to randomly generated non-disaster points ]))<laos_grid>


== Climate and development time series.

We model two types of time series: climate and development indicators in order to obtain future projections.

For the climate ones, we use:

- Total atmospheric CO₂ accumulation (in gigatons) @noaa_co2_2024
- Mean ocean temperature @zhang_noaa_2019.
- Country level mean monthly precipitation.


For the country development indicators, we extract from the World Development Indicators [@worldbank_wdi_2024]:

- Real GDP in USD millions.
- Population in millions




Figure @time_series_trend shows the temporal evolution of the variables included in the time series analysis. To deal with the trends and facilitate estimation, we standardize the data and compute the series first differences, @time_series_diff_trend in the annex present the plots of this transformed. The descriptive statistics for the transformed time series and their respective kernel density plots are presented in @time_series_sum and @time_series_kden respectively. It is necessary to comment that the Exponential Trend Smoothing (ETS) model used does not require the time series to be stationary.




  #figure(image("../images/eda/time_series_trend.png", width:120%),
caption: title_and_note(
  title:[Time series evolution through time],
  note:[Poulation is messured in millions, real GDP in millions of USD, CO2 in Gigatones, ocean temperature deviation from its mean in farenheit degrees, and precipitation deviation is the whole year monthly mean in millimeters],))<time_series_trend>












// == Climate time series

// @time_series_sum_table_a presents the summary statistics for the three climate time series used in the model: precipitation. For modeling purposes, we use the de-trended versions of these time series; @time_series_plot plots the behavior of these de-trended time series through time. We explored the stationarity by applying Augmented Dickey Fuller tests; we also analyzed the existence of cointegration relationships by applying Johansen and Engle-Granger cointegration tests. Results for all the tests are presented in Annex 1. For all the cases, we discarded the null hypothesis of non-stationarity and cointegration.

// #include "../tables/time_series_sum_table.typ"


// #figure(
//   image("../images/time_series_plot.png", width: 100%),
//   caption: [
//    De-trended climate time series through time
//   ],
// ) <time_series_plot>



// == Geospatial information

// * Country shapefiles*


// #figure(
//   image("../images/plain_shapefiles.png",  width: 110%),
//   caption: [
//    Latitude and Longitude for disasters
//   ],
// ) <shapefiles>

// To estimate the model, we take the shapefile of the region or country of interest, and we split it into a grid of 200 x 200 points. For each one of these points, we will calculate the geospatial variables, and then we will combine those points with the disaster data points to estimate the model. As mentioned, we will use as an example the case of Laos and its neighboring countries, Cambodia, Thailand, and Vietnam. @laos_neigh_grid presents the grid used for estimating the model on those countries.


// #figure(
//   image("../images/laos_neigh_grid.png",  width: 120%),
//   caption: [
//    Latitude and Longitude for disasters
//   ],
// ) <laos_neigh_grid>




// * Geospatial disaster data*

// EM-DAT data sets contain information regarding the disaster location in two different formats: First, it includes, for some observations, the exact coordinates of the disaster; second, it includes the names of the places and regions affected by the disasters. The information on the places and regions affected by the disasters is available for almost all the observations. However, the information regarding the coordinates is only available for 20% of the observations corresponding to the disaster types under analysis.

// To address this problem, we built an automated query to OpenAI's gpt4-mini model @openai2024gpt4omini asking to provide the set of coordinates corresponding to the locations indicated in the EM-DAT data set. Given the fact that some disaster observations contain multiple places of impact in the data set, for a unique disaster we obtain multiple coordinates in some cases. By including the obtained locations, we obtain a total of 22173 locations for the 4140 events. @disaster_map presents the coordinates representation over coordinates.

// #figure(
//   image("../images/disaster_map.png",  width: 110%),
//   caption: [
//    Disasters geospatial distribution across world-map
//   ],
// ) <disaster_map>

// Going back to the example case, we present on @laos_neigh_disasters the disaster points for Laos, Vietnam, Cambodia, and Thailand. For these countries, floods and storms represent 90% of the registered events.

// #figure(
//   image("../images/laos_neigh_disasters.png" ,  width: 110%),
//   caption: [
//    Disasters geospatial distribution for Laos, Cambodia and Thailand
//   ],
// ) <laos_neigh_disasters>


// @laos_disasters_zoom Presents a zoom-in on the reported disasters for Laos with their respective years of occurrence.

// #figure(
//   image("../images/laos_disasters_zoom.png",  width: 110%),
//   caption: [ Reported disasters for Laos with the correspondent year of occurrence
//   ],
// ) <laos_disasters_zoom>



// * Distance with rivers and coastline*

// Once the point grid of the region of analysis is created, we take use the world shapefiles to compute the distance of every point with the nearest coastline. This way, for every point of the map, we transform the location into a quantitative variable that can be introduced in the probabilistic model.

// For the rivers, we use a similar approach. From the HydroSHEDS database @lehner_global_2013, we obtain the coordinates for all the rivers around the world. Using one criterion, we filter the rivers to have those with the greater probability of causing floods: we include only the rivers with a long-term average discharge greater than 100 m³. Which refers to rivers that have in the data set the ORD_FLOW variable smaller than 5.


// #figure(
//   image("../images/rivers.png" ,  width: 110%),
//   caption: [
//    World rivers with a long-term average discharge greater than 100 m3
//   ],
// ) <rivers>


// Using the river data set, we compute for every point in the grid of the region of interest the distance to the closest river and coastline, which allows us to transform the geospatial information into quantitative variables that we will feed into the model. Continuing with the use case for Laos, Vietnam, Cambodia, and Thailand, we present on @laos_neigh_distances a visualization of the distance with rivers and coastlines. Interestingly, by plotting the distance with rivers, we obtain the shapes of the corresponding rivers.

// #figure(
//   image("../images/laos_neigh_distances.png" ,  width: 90%),
//   caption: [ Distance to closest river and coastlines for a 200 by 200 grid version of Laos, Vietnam, Cambodia and Thailand's maps.
//   ],
// ) <laos_neigh_distances>

// In @laos_neigh_distances, we observe a close-up into these variables for Laos, alongside the map of the rivers complying with the threshold of a long-term average discharge greater than 100 m³ established for the analysis.

// #figure(
//   image("../images/laos_distances.png",  width: 120%),
//   caption: [ Rivers and, distance to closest river and coastlines  grid version of Laos' map.
//   ],
// ) <laos_distances>





// #pagebreak()
