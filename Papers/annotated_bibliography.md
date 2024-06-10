### [Climate Change and Natural Disasters](https://repositorio.uchile.cl/bitstream/handle/2250/138715/Climate-Change-and-Naturaldisasters.pdf?sequence=1)
#### Authors
Ramón E. López, Vinod Thomas, Pablo Troncoso

#### Keywords:
Climate, Natural Disasters, Climate-Hazards, Sustainable Development, Government Policy

#### JEL Classification:
Q54, Q56, Q58, C22

#### Summary

The authors do an econometric analysis of trends in natural disaster frequency, as a function of global climate change. See `data_nodes_for_recreation.md` for details.

Main regressions:

1. Poisson/Negative Binomial regression on the number of events:

$$\mathbb E_t[y_{i,t}] = \exp(\beta_0 + \beta_1 U_{i,t} + \beta_2 V_{i,t} + \beta_3 W_{i,t} + \beta_4 Z_{i,t} + \beta_5 G_t) $$

2. Cointegration analysis of time fixed effects on climate change measures

$$ y_t  =\mu + \beta_x_t + \mu$$

Conveted to ECM form:
$$\Delta y_t = \delta + \lambda_1 \Delta y_{t-1} + k_0 \Delta x_t + k_1 \Delta x_{t-1} + \gamma_1 y_{t-1} +\gamma_2 x_{t-2} + \varepsilon_t$$
