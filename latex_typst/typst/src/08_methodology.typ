#import "../shared_functions.typ": title_and_note

= Methodology

== Uncertainty Quantification

Uncertainty quantification lies at the heart of our modeling approach. The disasters damage data has usually positive skew and and long right tails, which means that a small number of disasters can cause extreme damages.As a result, the mean and mode values fail to represent in detail reality. This makes the traditional approach of computing mean values uninteresting from a policy perspective. Instead, it is the _tails_ of the distribution that demand attention. As a result, we turn to generative probabilistic modeling as our tool of choice @gelman1995bayesian. Using a generate approach is crucial, because it allows us to simulate full distributions of potential outcomes, taking into account a specific functional relationships, prior research, and data.

Uncertainty quantification lies at the heart of our modeling approach. Disaster damage data typically exhibits positive skew and long right tails, where a small number of extreme events drive the majority of observed impacts. Consequently, traditional mean-based metrics fail to capture the reality of catastrophic risk. Instead, it is the tails of the distribution that demand attention. To address this, we employ generative probabilistic modeling @gelman1995bayesian as a framework for causal inference. This approach allows us to move beyond passive observation and perform counterfactual interventions using Judea Pearl’s do-operator @pearl2009causality. By simulating the full distribution of potential outcomes under the intervention $ P("Damage" mid(|) upright(d o)("Policy")) $, we can conduct rigorous scenario analysis that accounts for functional relationships, prior research, and the inherent uncertainty in the data.

While many generative frameworks exist, PyMC @abril2023pymc focuses on Bayesian generative models. This means that not only do our models output probability distributions, we also specify probability distributions over model parameters. These parameters, jointly denoted $theta$, can then be updated according to Bayes' theorem:

$ p(theta | X, cal(M)) = (p(X | theta, cal(M)) p(theta | cal(M))) / (integral p(X | theta, cal(M)) p(theta | cal(M)) dif theta) $

Where $X$ is observed data and $cal(M)$ is a model parameterized by $theta$. The left-hand quantity, $p(theta | X, cal(M))$, is an updated belief about the possible parameter values that $theta$ could take on, given that we've seen data $X$. This is called a _posterior_. The integral in the denominator of this expression is the sum of every possible parameter vector that could have given rise to the observed data, weighted by how likely we believe each parameter vector to be. This is infamously impossible to compute. Instead, the posterior can be approximated using sequential sampling schemes known as Markov Chain Monte Carlo (MCMC) algorithms. PyMC offers state-of-the-art MCMC algorithms, notably the No-U Turn Sampler (NUTS) @hoffman2014no.

The posterior is not the central object of interest in our research. Instead, we are interested in the range of possible disaster impacts that are implied by that posterior. This leads us to the _posterior predictive distribution_:

$ p(y | X, cal(M)) = integral p(y | X, theta, cal(M)) p(theta | X, cal(M)) dif theta $

Where $y$ is a new piece of data, not included in $X$. This expression marginalizes the uncertainty arising from the posterior, and gives a parameter-free probability distribution over possible outcomes, given the modeling framework and the input data. Armed with the posterior predictive distribution, we can answer important distributional questions. This will be extremely useful for building damages curves and damage curves predictions, as we explain next.

== Modeling disaster frequency:

As a first step, we model disaster frequency at country level. We use disaster data  from the EM-DAT data set @cred_emdat_2024. We model the number of disasters a country experiences per year as a function of climate variables and country-level development indicators. We focus on one type of disasters: hydrometeorological (storms, floods, and movements of wet masses).

To model the number of disasters we use a Zero Inflated Binomial probability distribution, which allows us to better capture the fact that the generative process of disasters has a big mass concentration around zero, as multiple years do not report disasters for several countries. Consequently, we can say that the number of disasters occurring in country $i$ on year $t$ is distributed according to the Zero Inflated Binomial probability distribution:

\

$
Y#sub[i,t] \~  "ZeroInflatedBinomial"(Psi,mu ,alpha  )
$

\
The Zero Inflated Binomial probability is completely defined by three parameters:

#set list(indent: 15pt, spacing: 2em)

- Inflation Parameter $Psi$: represents the probability of an observation being an excess zero. It models the likelihood that a zero count comes from the zero-generating process rather than the Binomial process.
- Mean parameter $mu$: This is the mean parameter of the Negative Binomial distribution. It represents the average number of events (or counts) you would expect to see if the observation is not an excess zero.
- Variance parameter ($alpha$): This is the dispersion parameter of the Negative Binomial distribution. It controls the variance of the distribution. Smaller values of α lead to more over-dispersion (greater variance relative to the mean), while larger values make the distribution approach a Poisson distribution.

Each of these three parameters is modeled with a probability distribution. In this way, we have a nested structure in which the Zero Inflated Binomial distribution that accounts for events frequency is expressed as a function of other three probability distributions. It is typical when working with a GLM to make the expected value $mu$ the center of attention in the model, by writing it as a transformed linear function of data. The present study is no exception. We model $mu = EE [Y_(i,t) | X, theta]$, the expected count of disasters in country $i$ during year $t$, as a function of observed covariates and parameters $theta$.


To model $Psi$, the probability of observing zero disasters for a given country-year tuple, we use a Beta probability distribution. The Beta distribution is a family of continuous probability distributions defined on the interval $[0,1]$. It is parameterized by two positive shape parameters, typically denoted by $alpha$ and $beta$, which we will denote with $tilde(alpha)$ and $tilde(beta)$, to differentiate them from parameters in the latent linear model of $mu$:


$
f(x|tilde(alpha), tilde(beta) ) =
frac( x^(tilde(alpha) -1) * (1-x)^(tilde(beta) -1 ) ,
      B(tilde(alpha), tilde(beta)))
$

Where $B(tilde(alpha), tilde(beta))$ is a normalization function of the form:

$
B(tilde(alpha), tilde(beta)) = integral_0^1 s^(tilde(alpha) -1) (1-s)^(tilde(beta))-1) dif s
$


To model the $alpha$ parameter we use a Gamma probability distribution. The Gamma distribution is a two-parameter family of continuous probability distributions. It is widely used in statistics due to its flexibility in modeling positive, continuous data. The Gamma distribution is strictly positive and completely defined by three parameters:

#set list(indent: 25pt)
- Shape parameter $k$: This parameter influences the shape of the distribution. It is also known as the "shape factor."
- Scale parameter $theta$: This parameter scales the distribution.

The full probability density function is given as:

$
f(x|k, theta) = frac(x^(k-1) e^(frac(-x, theta)),
theta^k Gamma(k))
$

Where $Gamma(k)$ correspinds to the Gamma function

$
Gamma(k) = integral_0^\u{221E} t^(k -1)e^(-t) d t
$


Now we move to the core of the model, which is given by the parameter $mu$, which we use to link a linear model to the expected disaster frequency. We assume the relationship between $mu$ and the observed covariates $X$ is linear in some latent space. A link function is chosen to transform the latent linear space to the space of observations, which is strictly positive. Thus, for every country $i$, in every year $t$, we compute $mu_(i,t)$ using the functional form:

$
mu_(i,t) = "softplus"(Z_(i,t))
$

Where $Z_(i,t)$ is the latent "rate" at which we observe disasters, modeled as a linear function of data. The $"softplus"$ function is a continuous approximation of the function $f(x) = max(0, x)$#footnote[This max function is called the ReLU function in the deep learning literature. In the GLM literature, the canonical link function for a Zero Inflated Binomial is the exponential function. We use softplus for its superior numerical properties. In particular, we did not want exponential blowup in the mean with respect to the input data.]:

$
"softplus"(Z_(i,t)) = log(1+ e^(Z_(i,t)))
$

Where we define the latent rate $Z$ as the sum of three components:

$
Z = "country_fixed_effect"_(i) + "spatial_random_effect"_(i) + "covariates_effect"_(i,t)
$

These components have the following meanings:

- $"country_fixed_effect"$ is a model intercept with a country hierarchy. This means that it is modeled using a Bayesian hierarchical framework, which serves as an intermediary between the extremes of no-pooling (independent OLS per country) and complete pooling (a single global intercept). This structure assumes that country-level intercepts are drawn from a common global distribution, allowing for partial pooling of information across units. For countries with sparse data or extreme outliers, the hierarchical prior induces shrinkage of the country-specific estimates toward the global mean. This "information sharing" significantly improves the reliability of estimates for small-sample countries, effectively reducing the noise and over-fitting.


- $"spatial_random_effect"_(i) $ accounts for spatial autocorrelation. To account for spatial autocorrelation, we incorporate a Besag-York-Mollié (BYM) specification @besag1991bayesian. This approach decomposes the $"spatial_random_effect"_(i)$ into a mixture of two distinct components to distinguish between regional trends and localized anomalies:

  - A global latent spatial term $tilde{theta}$. Captures global, unstructured variation. If a country behaves very differently from its neighbors (e.g., due to policy, geography, or data quality), this term allows for that deviation.
  - A structured spatial term from an Intrinsic Conditional Autoregressive (ICAR) model $\u{03C6}$. The ICAR model assumes that the value of a country’s spatial random effect is similar to that of its neighbors. Mathematically, this is a Gaussian Markov Random Field (GMRF) with dependence defined through an adjacency matrix $W$. This structure introduces local smoothing: nearby countries’ effects "pull" each other.

These two terms combined using a convex combination (weighted average) determined by $\u{03C1}$, a mixing coefficient. This way the full functional form of the $"spatial_random_effect"_(i) $ is:

To account for spatial autocorrelation, we incorporate a Besag-York-Mollié (BYM) specification @besag1991bayesian. This approach decomposes the $"spatial_random_effect"_(i)$ into a mixture of two distinct components to distinguish between regional trends and localized anomalies:An unstructured latent term $theta_i$: Captures "global" or idiosyncratic variation. If a country’s disaster profile deviates significantly from its neighbors—perhaps due to unique national policies or geographic features—this term absorbs that independent variance.A structured spatial term $phi_i$: Defined by an Intrinsic Conditional Autoregressive (ICAR) model. This component assumes that a country’s risk is conditional on its neighbors, functioning as a Gaussian Markov Random Field (GMRF) where dependencies are defined through an adjacency matrix $W$. This structure induces "local smoothing," effectively allowing nearby countries to share information and "pull" each other's estimates.Following the modern BYM2 refinement, these terms are combined via a convex combination determined by a mixing coefficient $rho$. This parameter quantifies the proportion of the total spatial variance attributable to the structured component versus the unstructured noise.




$
"spatial_random_effect"_(i)  = sqrt(1-\u{03C1})  \u{00B7} tilde(theta)_i + sqrt(frac(\u{03C1},s ) \u{03C6}_i)
$

With $s$ a scaling factor that ensures that the variance of the ICAR component is appropriately normalized.

For the $"covariates_effect"_(i,t)$ we introduce the time dimension $t$, and we use the next covariates:

- $"ln_population_density_standardized"_(i,t)$: log of population density for country $i$, period $t$.
- $"ln_gdp_pc_standardized"_(i,t)$:  log of GDP per capita for country $i$, period $t$.
- $"population_standardized"_(i,t)$: Population in millions for country $i$, period $t$ squared.
- $"precip_deviation_standardized"_(i,t)$: Deviation of precipitation on country $i$ on period $t$ from its trend.
- $"co2_standardized"_(t)$: Worldwide atmospheric CO2 concentration in parts per million at period $t$.

\

\
To control for unobserved heterogeneity on the panel structure, we apply the Mundlak adjustment by introducing group-level (country-level) random slopes for each covariate, which allows the model to account for correlation between covariates and latent group-specific effects. This way, the covariates functional form has the structure:

$
"covariates_effect"_(i,t) = \u{2211}_(j=0)^n X_(i,t,j) \u{22C5} \u{03B2}_j +  \u{2211}_(j=0)^n \u{03BB}_(i,j) \u{22C5} \u{03B2}_j^("latent")
$

Where:
- $i$ corresponds to country index, $t$ year index, and $j$ covariate index.
- $\u{03BB}_(i,j)$ is a country-specific deviation (random slope) for covariate.




== Modeling disaster damages

For disaster damage, we use the logarithm of disaster damage. We model this variable using a Hurdle LogNormal probability distribution. The Hurdle LogNormal distribution is a type of hurdle model used to handle zero-inflated continuous data. Hurdle models are particularly useful when dealing with datasets that have an excess of zero values, in addition to continuous positive values. The Hurdle LogNormal model specifically combines a binary process that models the zeros and a truncated LogNormal process that models the positive continuous values.

The overall likelihood for the Hurdle LogNormal model is the product of the likelihoods from the binary component and the truncated LogNormal component:

#align(center)[- $p$ if $y_i = 0$]
#align(center)[- $(1-p)*"LogNormal"(y_i|mu, \u{03C3})$ if $y_i \u{2260} 0$]

Here, the LogNormal component is completely defined by the parameters $mu and, \u{03C3}$.To model sigma, we use a Half Normal distribution, which ensures strictly positive terms. While for $mu$, we use exactly the same linear structure we used for frequency $mu$ on equation 10.

== Modeling geospatial patterns of disasters

As mentioned previously, the geospatial component is estimated using data from a specific region only, and predictions are generated only for a single target country at a time. This approach is necessary due to the substantial computational resources required to estimate the model at a global scale. To illustrate the methodology, we present results for two countries: Laos and Costa Rica.

In the case of the probability of the event model, the objective is to model the probability of one event happening at any point of a country's grid.To achieve this, we create a set of synthetic non-disaster points, and we train the model to identify the probability of a point being a real disaster or a synthetic non-disaster point.

We estimate two different model versions. The first uses only the coordinates  ($"latitude"$ and $"longitude"$) of the grid and disaster points to capture geographical patterns of disaster occurrence. It captures these patterns by applying a Hilbert Space Gaussian Process (HSGP).

The second one incorporates, on top of the HSGP model, the distance to rivers and coastlines variables, plus a set of country-level covariates and climate-related time series.

In both cases, we estimate the probability of occurrence of an event by using a logit regression estimated in a Bayesian framework with PyMC @abril2023pymc. Therefore, we model the probability of an event happening at  location $g$ in country $i$ at time $t$. This way, the general specification corresponds to the general form:

$ P(Y=1 | X)_("i,g,t") = sigma( "country_fix_effect"_i + "HSGP"_("i,g") + X_("i,g,t")*beta_("i,g,t") ) $

Where:

- $sigma(Z)$ corresponds to the logistic function $frac(1, 1 e^(z))$.

- $"country_fix_effect"_i$ represents the country fix effect for country $i$.

- $"HSGP"_(i,g)$ is the Hilbert Space Gaussian Process component that will be explained next.

- $X_(i,t)*beta_(i,t)*$ corresponds to a set of covariates and their parameters, where we include three types of covariates: geospatial, climate time series, and country-level macro variables.


*Hilbert Space Gaussian Process*

The *Hilbert Space Gaussian Process (HSGP)* is an approximation method used to represent a Gaussian Process (GP) in a computationally efficient manner. Traditional GPs require inverting an \( N \times N \) covariance matrix, which becomes computationally expensive for large datasets. HSGP approximates the GP using a finite basis function expansion, reducing the complexity.

The function $phi_k(x)$ and the corresponding spectral densities $lambda_k$  to approximate the GP prior:  \

$
f(x) approx sum{k=1}^{m} beta_k sqrt(lambda_k) phi_k(x)
$

where:
- $beta_k ~ NN(0,1)$are the basis coefficients.
- $lambda_k$ are the eigenvalues derived from the covariance function.
- $phi_k(x)$ are the basis functions, which capture spatial variations.

#v(2em)

Our model applies an HSGP prior to analyze the probability of a geospatial location given by $ "lat", "long"$ of  experiencing a climate-related disaster. The key components are:

1. *Spatial Covariance Function:*
   $ k(x, x') = eta^2 K(x, x'; ell) $
   where $eta$ is a scale parameter and $ell$ is the length scale, drawn from a lognormal prior.

2. *Hilbert Space Representation:*
   - The GP is approximated using a $"Matern-5/2" "kernel"$ with parameters $( m_0, m_1 \)  $ controlling the number of basis functions. We use 35 as a value for both parameters.
   - The basis function matrix $Phi$ and spectral density $sqrt(lambda)$ define the GP prior:
   $  Phi, sqrt (lambda)= "gp.prior"_"linearized"(X)  $


3. *Deterministic Component:*
$ "HSGP"_"component" = Phi dot (beta dot.circle sqrt(lambda) ) $

   where $beta ~ N[0,1] $  are the basis coefficients.

4. *Bernoulli Likelihood:*
   - The probability of a disaster occurring at a given location is modeled as a $"Bernoulli"$ process with a logit link:

   $ p = "HSGP"_"component", y ~ "Bernoulli"(sigma(p))  $

     where $sigma(p) $  is the logistic function mapping to probabilities.


Given this specification, the HSGP model leverages geospatial coordinates ($"latitude"$ and $"longitude"$) as inputs, allowing it to learn spatial dependencies in disaster occurrences. By reducing computational complexity, HSGP enables inference on large datasets where standard Gaussian process methods would be infeasible. The prior structure ensures smooth spatial predictions, capturing meaningful regional variations in disaster risk. This whole setup allows the model to capture the likelihood of climate-related events in different regions while maintaining scalability.


*Full model specification*

In this second step, we estimate the fullmodel specification
$ P(Y=1 | X)_("i,g,t") = sigma( "country_fix_effect"_i + "HSGP"_("i,g") + X_("i,g,t")*beta_("i,g,t") ) $

Here, in addition to the geospatial pattern detected by the HSGP, we obtain for every point in the grid of the region analyzed and for every disaster point the variables corresponding to 3 sets of covariates: climate change series, country-level specific variables, and distances to rivers and coastlines. All the covariates we introduce here are standardized to simplify the scale manipulation and the prior setting in the estimation. The standardization is done based on the whole model data set's mean and standard deviation. All the priors of the parameters are defined as normal distributions with mean zero and standard deviation one.

\
#underline[Climate change series]:
- $"co2_standardized"_(t)$: Worldwide atmospheric CO2 concentration in parts per million at period $t$.
- $"dev_ocean_temp__standardized"_t$: Deviation of the mean world's ocean temperature from its trend on period  $t$.
- $"precip_deviation_standardized"_(i,t)$: Deviation of precipitation on country $i$ on period $t$ from its trend.


\
#underline[Country-level specific variables]:

- $"ln_population_density_standardized"_(i,t)$: log of population density for country $i$, period $t$.
- $"ln_gdp_pc_standardized"_(i,t)$:  log of GDP per capita for country $i$, period $t$.
- $"square_ln_gdp_p_standardized"_(i,t)$: log of GDP per capita for country $i$, period $t$ squared.
- $"population_standardized"_(i,t)$: Population in millions for country $i$, period $t$ squared.

\
#underline[Distances to rivers and coastlines]
- For each point of the map, we compute the distance with the closest river, and we  introduce its log as a feature "$"log_distance_to_river__standardized"_(g)$

- We also compute the distance to the closest coastline, and we include its log as a feature: $"log_distance_to_coastline__standardized"_(g)$




== Modeling patterns of climate and development indicators

With the objective of being able to make predictions, we use a State Space modeling framework to predict trends in key inputs of the model. In particular, we use the implementation of State Space modeling via PyMC @pymc-extras-statespace In particular we project for a specific country of analysis: real GDP, population, deviation from trend precipitation. Additionally we project the global variables: atmospheric CO₂ accumulation, and ocean temperature deviations from trend.


For this, we employ a Bayesian dynamic linear model based on the PyMC state-space module, using a Bayesian Exponential Time Smoothing (ETS) @ets_time_series approach. This approach enables probabilistic inference and forecasting under a fully Bayesian framework. We model the multivariate time series using an additive trend exponential smoothing state-space model with the following configuration: local level $(A)$, damped local trend $("Ad")$, and no seasonal component $"(N)"$. The model specification includes measurement error, a dense innovation covariance structure for the state shocks, and a stationary initialization with dampening. This setup provides flexibility to accommodate a wide range of time-varying behavior, including long-run stochastic trends, persistent shocks, and changing volatilities across the multiple indicators.

Formally, let $y_t ∈ \u{211D}^n$ denote the observed vector of the $n$ variables at time $t$
t, which evolves according to a linear Gaussian state-space system:

$
y_t = Z\u{03B1}_t + epsilon_t," " epsilon ~ Nu(0, H)

\
alpha = T alpha_(t-1) + R theta_t, ~ theta_t Nu(0, Q)

$
where $alpha$ is the latent state vector (e.g., level and trend components), $H$ is the measurement error covariance matrix, and $Q$ is the innovation covariance matrix for the state shocks. These are learned from the data via a hierarchical prior specification, as described below.


* Prior Elicitation with Maximum Entropy Transformations*
To reflect informed but flexible beliefs about key smoothing and structural parameters, we employ maximum entropy–transformed priors (pz.maxent) for most hyperparameters. This allows us to specify constrained, information-efficient priors that respect known bounds or regularities (e.g., positivity, bounded damping).


*Multivariate Covariance via LKJ Prior*
We place an LKJ prior on the Cholesky decomposition of the state innovation covariance matrix $Q$, allowing for correlated innovations across state dimensions (e.g., co-movements between economic and climate variables). Specifically, we decompose
* Q=LL^T *, where $L$ is the lower triangular Cholesky factor, and the standard deviations and correlations are separately inferred. We set the concentration parameter $η=4$
, favoring weakly correlated structures but allowing for flexibility in learning strong correlations if supported by data. The standard deviation terms are assigned Gamma priors constrained to lie within plausible bounds.

*Forecasting*


Posterior Inference and Inverse Transformation
The model is then fit to data using Hamiltonian Monte Carlo (HMC) sampling via the nutpie backend @nutpie2023 with jax acceleration @jax2018. The forecasts and trajectories generated by the model are returned in standardized space; hence, we apply an inverse exponential transformation composed with a `StandardScaler` inverse to convert model outputs back into the original data units.



== Country-level damage curves

Once we computed the probability distributions of event frequency, and the probability distribution of damages from points 4.2 and 4.3, the expected damages can be be easily computed as a product of both.

$
P("expected_damage")_(i,t) = P("frequency")_(i,t) * P("damages")_(i,t)
$

One advantage of this approach, and the bayesian computations method we use, is that allows us to propagate and quantify uncertainty from the initial two models to the expected damages.

Now that we have the expected damages, we resort to the notion of *return years* (RY)  to represent the results in a much more intuitive way. A 100-RY disaster is one the associated damage of which is expected to be equaled or exceeded once every one-hundred years. Our primary object of study is, thus, a damage curve expressed in return years. The left panel of @example_curve shows an example distribution over damages for a given year. The x-axis shows possible damage values, while the height is the probability density at that damage. Based on this curve, we can create a quantile function, which maps probabilities (on the x-axis) to the damage value which is larger than that percentage of values. The 100-RY damage value is larger than 99% of all damage values produced by this distribution, and is marked.

#figure(image("../images/example_damage.png", width:100%),
caption: title_and_note(
  title:[Example Damage Curve for a Single Year and Disaster Type],
  note:[The left curve shows all possible damage outputs for a category of disaster (e.g. flood, earthquake, drought, etc.). The x-axis shows the possible dollar-denominated damages, while the y-axis shows the probability density associated with that damage value (higher = more probable). The black bar shows the largest interval containing 95% of all possible outcomes (called the 95% HDI). The right curve shows the quantile of the distribution on the left. The 100-RY disaster, associated with the 99% quantile, is marked ],
  short_title:[Example Damage Curve]))<example_curve>

Several features of @example_curve are worth pointing out. The curve has a lot of mass around zero, followed by a long tail. Large disasters are, after all, relatively rare, with many years seeing none at all. As a result, the mean of the distribution (marked with an open circle on the left plot) is not at all interesting from a policy perspective. Instead, we are interested in quantifying the density in the _tail_. Note that the 100-RY disaster, with a value of 4.1, is already a very rare event. But we can also contemplate even rarer events. In this example, a 500-RY event would have a value of 5.68. As the tail of the distribution becomes fatter, the difference between sizes of these rare events becomes larger.

Of primary interest to us is how climate change can potentially shift these curves, and how the vary according to geospatial patterns.

Climate researches expect disasters to become both _more severe_ and _more frequent_ as the climate changes. We reason about these possibilities separately, by decomposing the problem in two parts



As explained, the distribution
shown in @example_curve is computed by using two probability distributions: the probability distribution of seeing events, and the probability distribution of damages in case an event happens. Formally, we denote $D: Omega arrow R^+$ as a random variable representing annual disaster damage, _conditional on a disaster occurring_. In addition, denote $P: Omega arrow [0, 1]$ as the probability of a disaster occurring. Their joint probability distribution is defined as:

$ f_(P,D) (p,d) = f_(D | P) (d | p) f_P (p) $

This form allows for a shift in either the _frequency_ of disasters, represented by $f_P (p)$, or the _severity_ of disasters, represented by $f_(D | P) (d | p)$. To complete the model, we introduce a Bernoulli distributed random variable $I: Omega arrow {0, 1}$ with probability mass function:

$ f_(I | p) (i | p) = cases(p & "if" i = 1, 1 -p  & "if" i =0) $

The full model is thus:

$ f_(D, I, P) (d, i, p) = f_(D | I, P) (d | i, p) f_(I | P) (i | p) f(p) $

The damage curve we observe in the data is the marginal distribution over damages, obtained by integrating over both $P$ and $I$:

$ f_D (d) &= integral_0^1 sum_(i in {0, 1}) f_(D, I, P) (d, i, p) dif p \
&= integral_0^1 f_(D, I, P) (d, i=0, p) dif p + integral_0^1 f_(D, I, P) (d, i=1, p) dif p
$

When $i = 0$, $d = 0$ by definition, so the expression simplifies significantly:

$ PP(D =0) & = integral_0^1  f_(I | P) (i = 0 | p) f(p) dif p \
&= integral_0^1 (1 - p)  f(p) dif p \
&= integral_0^1 f(p) dif p - integral_0^1 p f(p) dif p
$

The first term here is 1, because $f(p)$ is a probability distribution. The second term is exactly the expected value of $P$. Defining $EE[P] = mu = integral_0^1 p f(p) dif p$, the point mass on zero is simply:

$ PP(D =0) = 1 - mu $

On the other hand, when $i = 1$ then $d > 0$ and:

$
f_D (d) &= integral_0^1 f_(D, I, P) (d, i, p) dif p \
&= integral_0^1 f_(D | I, P) (d | i=1, p) f_(I | P) (i=1 | p) f(p) dif p \
&= integral_0^1 f_(D | I, P) (d | i=1, p) (p) f(p) dif p
$

Assuming $D$ and $P$ are conditionally independent given $i=1$, this expression becomes:

$ f_D (d) = f_(D | I) (d | i = 1)  integral_0^1 p f_P (p) dif p $

Once again the expected value of $P$ appears, allowing the follow simplification for the marginal distribution over disasters:

$ f_D (d) = cases(mu dot f_(D |I) (d | i = 1) & "if" d > 0,
1 - mu & "if" d =0 )
$

This is a zero-inflated mixture model with a point-mass on zero representing the years with no disaster. Written this way, the two proposed mechanisms to increase disasters are clear. When disasters become more frequent, it implies that $mu$ becomes larger. This increases the multiplier on the damage term $f_(D, I) (d, i=1)$, and shrinks the probability of not having a disaster. On the other hand, when disasters become more severe, it only scales up the damage term, while leaving the probability of not seeing a disaster unchanged. In either case, the expected damages from disasters increases. Starting from the definition of the expected value:

$ EE[D] &= integral_0^infinity d f_D (d) dif d \
&= 0 dot (1 - mu) + mu integral_0^infinity d f_(D |I) (d | i = 1) dif d \
&= mu EE[D | I =  1]
$

Again it is clear when $mu$ becomes larger, the expected damages increase. Furthermore, $EE[D | I = 1]$ is the average severity of disasters. It is equally clear that when this increases, the $EE[D]$ also increases.

This formalism provides us a framework for thinking about the channels through which climate change can cause increased disaster risk. It is silent, however, on how to actually model the quantities of interest. For starters, $D$ and $P$ are not directly observed. We can only observe the disasters (storms, floods, etc) that actually happen, and try to infer something about their frequency over time. This frequency, however, is driven by many factors, including the climate, local geography where disasters are observed, as well as human activity, including economic activity. In addition, what we observe are imperfect proxies for the true quantities of interest, introducing additional layers of uncertainty. Here is where the causal assumptions presented in @causal_graph become highly relevant, as they provide a causal framework that justifies  the statistical models we ultimately employ to estimate $f_P (p)$ and $f_D (d)$.


== Geolocated damage curves

Once we have the country-level expected damages, we disaggregate these estimates spatially by leveraging our previously estimated probability of disaster occurrence at each geolocated grid point $g$. This allows us to construct geolocated damage curves, capturing how expected damages vary across space within each country. The key idea is to assign a share of national expected damages to each location, proportional to its relative disaster probability. This results in a spatially disaggregated risk map with expected damage curves for each grid point.

$
P("expected_damage")_(i,t,g) = frac( "P(Y=1 | X)(i,g,t) ", \u{2211}_g P(Y=1 | X)(i,g,t) ) * P("expected_damage")_(i,t)
$

This approach maintains internal consistency with the national-level expected damage figures. It distributes damages in proportion to the local probability of experiencing a disaster, as computed using our HSGP-based spatial event model. The denominator ensures the probabilities sum to one within each country-year, making the spatial distribution interpretable as a relative risk-weighted allocation. Importantly, this method inherits the full uncertainty structure of the Bayesian event and damage models, allowing us to construct local credible intervals around the expected damages at each location.

Once the expected damages are mapped at the local level, we proceed in a similar manner as before to construct geolocated damage curves. That is, for each location $g$, we generate the probability distribution over damage levels using the joint Bayesian posterior of both event probabilities and damage given an event. This yields a distribution $f_(D,g)(d)$  for each point $g$ from which we derive return-year quantiles (e.g., 100-RY or 500-RY events) for local areas.

Geolocated damage curves add critical granularity to the policy relevance of our framework. Different locations within a country face widely varying exposure and vulnerability profiles. For instance, coastal regions may face frequent flooding, while inland agricultural zones may suffer from drought. Our framework accounts for these spatial patterns by conditioning on local predictors such as distance to rivers, elevation, and population exposure, alongside the HSGP structure that learns spatial dependencies directly from the data.

Finally, a similar causal framework used to interpret country-level changes under climate scenarios applies locally. Increases in $P(Y=1 | X)(i,g,t)$ and $P("events")_(i,t)$ derive in more frequent local disasters (e.g., more floods in coastal towns), while changes in $P("damages")_(i,t)$ imply higher severity conditional on a disaster (e.g., stronger typhoons hitting a specific region). Spatially resolved return-year curves provide the basis for identifying which areas are most vulnerable, how risks change under counterfactual scenarios, and where targeted adaptation investments may be most needed.













#pagebreak()
