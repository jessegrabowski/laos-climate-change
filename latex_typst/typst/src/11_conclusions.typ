= Conclusions

This study introduces the Probabilistic Geospatial Risk (PGR) model, an end-to-end framework designed to quantify and project the frequency, economic damage, and spatial distribution of climate change-related disasters. By integrating Bayesian generative modeling, state-of-the-art spatial analysis, and hierarchical time-series forecasting, the PGR model transcends traditional national-level risk assessments. It provides granular, point-level estimates of disaster risk, enabling policymakers, researchers, and practitioners to identify high-risk areas and prioritize interventions.

The model’s ability to capture non-linear relationships and spatial autocorrelation through techniques like the Hilbert Space Gaussian Process (HSGP) and Intrinsic Conditional Autoregressive (ICAR) models provides valuable insights, while its use of generally available satelital information allows predictions even in data-scarce regions.

From Global Trends to Local Action
The PGR model’s outputs are highly actionable for climate adaptation and disaster risk reduction. By projecting return-year damage curves and geolocated risk maps, the model bridges the gap between global climate trends and local vulnerability. For example:

Laos and Costa Rica were used as case studies to demonstrate how the model can identify regions with escalating exposure to hydrometeorological disasters. The results reveal that both countries face increasing frequencies of extreme events, with Costa Rica experiencing a sharper rise in projected damages due to its economic and geographic vulnerability.

The geolocated return-year curves for specific locations (e.g., Desamparados, El Bambú, and Cariari in Costa Rica) illustrate how communities can use these tools to assess their unique risks and plan targeted adaptations, such as infrastructure upgrades or early warning systems.

The model’s ability to disaggregate national-level risks into local probabilities empowers governments to allocate resources more effectively, focusing on areas where climate impacts are projected to be most severe.

A core innovation of the PGR model is its emphasis on uncertainty quantification. Traditional risk assessments often focus on point estimates (e.g., mean or mode), which are insufficient for policy planning. In contrast, the PGR model leverages posterior predictive distributions to simulate the full range of possible outcomes, including tail risks. This approach is critical for understanding the potential for catastrophic events, which, while rare, can have outsized economic and humanitarian consequences.

The use of Markov Chain Monte Carlo (MCMC) sampling and Bayesian hierarchical modeling ensures that uncertainty is propagated through all stages of the analysis, from frequency and damage modeling to spatial risk mapping. This transparency allows decision-makers to evaluate not just the most likely scenarios but also the worst-case possibilities, fostering more resilient planning.


The study’s projections underscore the urgent need for climate action. Under business-as-usual scenarios, both Laos and Costa Rica are expected to experience:

 - Higher frequencies of hydrometeorological disasters, with return periods for extreme events shortening dramatically (e.g., 100-year events becoming 50-year events by mid-century).

 - Increased severity of damages, as rising ocean temperature temperatures and CO₂ concentrations amplify the intensity of storms, floods, and droughts.

 - Spatial shifts in vulnerability, with urban centers (e.g., Costa Rica’s Greater Metropolitan Area) and regions close to rivers facing disproportionate risks due to population density and geographic exposure.

These findings align with the broader scientific consensus that climate change will exacerbate disaster risks, but the PGR model provides the granularity needed to translate global trends into local action.
