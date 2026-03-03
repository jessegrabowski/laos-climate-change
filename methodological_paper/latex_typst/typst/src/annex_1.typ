#import "../shared_functions.typ": title_and_note

= Annex 1


#figure(image("../images/eda/geo_features_kden_ca.png", width:120%),
caption: title_and_note(
  title:[Kernel density and histogram of the geo-spatial model data set for  Costa Rica,  El Salvador,  Guatemala,  Honduras, Nicaragua and Panama],
  note:[All features, except for "is_disaster" have been standardized],
  ))<geo_features_kden_ca>


  #figure(image("../images/eda/geo_features_kden_laos_neigh.png", width:120%),
caption: title_and_note(
  title:[Kernel density and histogram of the geo-spatial model data set for  Cambodia, Thailand, Laos and Vietnam],
  note:[All features, except for "is_disaster" have been standardized],
  ))<geo_features_kden_laos_neigh>


#figure(image("../images/eda/time_series_k_den.png", width:120%),
caption: title_and_note(
  title:[Kernel density and histogram of the geo-spatial model data set for  Cambodia, Thailand, Laos and Vietnam],
  note:[],
  ))<time_series_kden>



#include "../tables/time_series_sum_table.typ"

  #figure(image("../images/eda/time_series_diff_plot.png", width:120%),
caption: title_and_note(
  title:[Time series evolution through time],
  note:[Poulation is messured in millions, real GDP in millions of USD, CO2 in Gigatones, ocean temperature deviation from its mean in farenheit degrees, and precipitation deviation is the whole year monthly mean in millimeters],
  ))<time_series_diff_trend>
