# OECD - Laos

Vars:

- Population density
    - https://data.worldbank.org/indicator/EN.POP.DNST
- GDP per capita (constant 2005 $)
    - https://data.worldbank.org/indicator/NY.GDP.PCAP.KD?name_desc=false
- Average precipitation deviation
    - Use 1 deg x 1 deg grid
    - Monthly,  Global Precipitation Climatology Centre (GPCC) Full Data Reanalysis (Version 7.0)
    - Departure from the average of its 30-year base period 1961-1990
- Average temperature deviation
    - HadCRUT3v (variance adjusted version)
    - Departure from the 30-year base period 1961-1990
- Population

Global vars:

- $\\text\{CO\}_2$ level
    - https://data.globalchange.gov/dataset/noaa-cmdl-co2_mm_gl
- $\\text\{CO\}_2$ deviation from level in 1970
- Sea temperature deviation
    - Departure from the 30-year base period 1971-2000
    - I can\'92t find the exact file they use (no login to FTP)
    - I suggest using this: https://www.ncei.noaa.gov/access/global-ocean-heat-content/monthly_analysis.html#null

Data sources:

14

Data filters:

- Reference paper: 1970 to 2013
- Reference paper: used only EM-DAT events with at least 100 deaths and directly affecting 1,000 people, controls for reporting bias
- I disagree with the logging, we should use log(x+1) instead so that a log of zero would not be undefined.

Questions:

What to do for countries that no longer exist/merged? (Soviet Union, West Germany, etc)
\