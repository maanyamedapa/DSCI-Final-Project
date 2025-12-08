
# DSCI Final Project  

#------Introduction -----

This project analyzes the relationship between bike lane density, transit dependency, and environmental justice scores across Los Angeles County census tracts by exploring how Bike lane accessibility and neighborhood characteristics relate to environmental outcomes.  

It uses the key environmental outcome variables of PM2.5 and CES Score from CalEnviroScreen data set. PM2.5 was chosen over the other environmental variables like Ozone score or traffic score because it captures observations on a more granular level ideal for bikelane evaluation. g

#----------------------DATA SOURCES -----------------------

| Data Source                   | Name / Short Description                               | Source URL                                                                                  | Data Type  | Rows       |
|:---------------------------- |------------------------------------------------------- | --------------------------------------------------------------------------------------------|----------:|:--------------|
| LA Metro ATSP Bikeways (2024) | Vector data showing bikeways in LA County               | https://data.lacounty.gov/datasets/la-county-bikeways-2024-metro-atsp/about                 | Shapefile  | 2,837 rows |
| LA Census Tracts              | LA County tract boundaries                              | https://data.lacounty.gov/datasets/2020-census-tracts-4/about                                | GeoJSON    | 2,496 rows |
| CalEnviroScreen Dataset       | Pollution burden and environmental justice scores       | https://oehha.ca.gov/calenviroscreen/report/calenviroscreen-40                               | CSV/Excel  | 7,892 rows |
| ACS 2023 5-Year Estimates     | Socio-economic and vehicle ownership indicators         | https://api.census.gov/data/2023/acs/acs5                                                    | API        | 2,067 rows |



● ——————Analysis ——————- 
1. Regression of bike lane density metric against CES Scores, showed significant negative correlation
Checked using Variance Inflation Factor (VIF). The VIF was approximately 1.0 for all key variables, indicating no multicollinearity issues. 
Heteroskedasticity- Checked and corrected for using robust Standard Errors. Significant negative correlation (P < 0.05)

2. Unsupervised Learning Model - K-means clustering utilized to create neighborhood typologies 

3. Mapping clusters onto LA County map showed priority zones with high enviromental burden and low bike lane access. Census tracts grouped into 5 distinct neighborhood types based on infrastructure, pollution, and socio-economic vulnerability. Green used for positive attributes like lower environmental burden score (CES Score) and high bike lane density. Red used for negative attributes like high CES score and low bike lane density. Mapping of CES scores and no-vehicle houshold rates support zones of priority suggested by the first map. There is a common pattern of high environmental burden and low active transport access. 

4. Box Plot- used to show a binary comparision between areas with bike infrastructure versus without

● ————————Summary of the results———————— 

1.  OLS Regression Results                            
==============================================================================
Dep. Variable:              ces_score   R-squared:                       0.060
Model:                            OLS   Adj. R-squared:                  0.059
Method:                 Least Squares   F-statistic:                     71.08
Date:                Sun, 07 Dec 2025   Prob (F-statistic):           1.54e-30
Time:                        18:58:54   Log-Likelihood:                -8371.9
No. Observations:                1986   AIC:                         1.675e+04
Df Residuals:                    1982   BIC:                         1.677e+04
Df Model:                           3                                         
Covariance Type:                  HC1                                         
===========================================================================================
                              coef    std err          z      P>|z|      [0.025      0.975]
-------------------------------------------------------------------------------------------
const                      35.0012      0.566     61.798      0.000      33.891      36.111
bike_lane_density_sq_mi    -0.3977      0.173     -2.300      0.021      -0.737      -0.059
median_income           -7.735e-09   6.33e-09     -1.223      0.221   -2.01e-08    4.66e-09
vehicle_rate              122.8733     10.306     11.923      0.000     102.675     143.072
==============================================================================


Interpretation: R^2 of 0.06 indicates the model captures only a small portion of CES score variation

1. Bike lane density has a small negative association with CES score and is statistically significant
2. Median income is not statistically significant and shows no meaningful relationship
3. Vehicle rate has a strong positive association with CES score and is highly significant
Interpretation
	•	Higher vehicle rates correspond with higher pollution burden scores
	•	Bike lane density shows a slight link to lower CES burden, but the effect size is small
	•	Income does not drive CES score differences in this specification

2. K-MEANS: The "Moderate" Majority -Cluster 2 Most of the census tracts in our data set fall into this category. These neighborhoods are characterized by a High Environmental Burden, yet they have a moderate-to-high presence of bike lanes. This suggests that although infrastructure is there, it has not yet offset the environmental challenges in these areas.
The "High-Priority" Zones (South LA): A clear cluster-often coming up as the most at-risk group-captures low-income areas, particularly in South LA. These tracts are characterized by a double burden  with high environmental burden and low bike infrastructure

3. Box Plot
	A. Environmental Burden by Infrastructure Presence
		•	Tracts with bike lanes have a lower median CES burden compared to those without bike lanes.
		•	Data spread is wider for tracts with bike lanes, suggesting more variation in environmental conditions within these areas.
		•	Tracts without bike lanes- higher median and upper quartile, generally more burdened
	B. Pm2.5 by bike lane presence 
		•	Bike lane presence has no meaningful relationship with PM2.5 concentration.
		•	Median PM2.5 levels are almost the same, little to no variation 
		•	Explanation- PM2.5 is driven by regional emissions, traffic corridors, industrial sites, and atmospheric conditions. Particulate matter travels far due to high windspeeds, cannot be reduced by bike lane presense alone

INSTRUCTIONS 
How to Download the Data:

1. CalEnviroScreen 4.0:

-Download the "Excel" version from the OEHHA Website.

-Rename it to CalEnviroScreenData.xlsx (if needed).

-Place it in data/raw/.

2. LA County Bikeways (2024 Metro ATSP):

-Download the Shapefile form the LA Metro Open Data Portal Link provided above

-Unzip all files (.shp, .shx, .dbf, etc.) into data/raw/.

-Ensure the main file is named LA_County_Bikeways_(2024_Metro_ATSP).shp.

3. Census Tracts:

- Download the LA County Tracts GeoJSON (EPSG:4326 or 3310).

- Save it as la_tracts.geojson in data/spatial/.

4. ACS Data:

No download required. The pipeline automatically fetches this from the Census API. Key not needed,


# Project Structure
* src: Contains all source code (main.py, load.py, analyze.py, config.py, etc.).
* tests.py: Tests for data processing.
* results: Output directory for maps, plots, and statistical tables.
*readme and requirements with instructions for data downloading and python libraries needed

## Installation

1. Install Dependencies:
   '''bash
   pip install -r requirements.txt

