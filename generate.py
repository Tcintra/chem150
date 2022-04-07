"""
This script generates our dataset for our machine learning model.

It currently hardcodes which site we will generate data for (LA North Main St.) in the AQS data, and
we use only daily data for 2018.

Our script first generates data for the CRITERIA pollutants and MET variables and saves as a CSV. It
then generates data for VOC compounds in the AQS dataset and their corresponding emissions data from
the CEDS dataset, saving each separately.
"""

import json
import pandas as pd
from data_fetcher import DataFetcher

PATH    = './data/clean/Los_Angeles-North_Main_Street/2018/'
SITE    = '1103'
COUNTY  ='037'
STATE   = '06'

datafetcher = DataFetcher()

# CRITERIA and MET variables
# core_df = datafetcher.create_dataset(20180101, 20181231, site=SITE, county=COUNTY, state=STATE, processed=True, verbose=False, vocs=False)
# core_df.to_csv(PATH+'core.csv')
# print("Finished core df.")

# AQS VOCS and corresponding emisions
final_vocs, final_emissions = datafetcher.get_final_compounds()

# NOTE: REMOVE m/p Xylene data as its indices are scrambled and so I assume the data is untrustworthy.
final_vocs.remove('m/p Xylene')

# vocs_df = datafetcher.get_voc_data(20180101, 20181231, STATE, COUNTY, SITE, final_vocs)
# vocs_df.to_csv(PATH+'vocs.csv')
# print("Finished vocs df.")

emissions_df = datafetcher.get_ceds_data('2018', keep=final_emissions) 
emissions_df.to_csv(PATH+'emissions.csv')
print("Finished emissions df.")
