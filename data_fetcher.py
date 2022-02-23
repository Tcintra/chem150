import requests
import pandas as pd
import random
import datetime

from preprocessing import Processor

EMAIL = "tcintra@hmc.edu" # Should transition to env
KEY = 'russetwren13'

URL = 'https://aqs.epa.gov/data/api/'

# Define some string constants for easy typing
SAMPLE_DATA_BY_SITE = 'sampleData/bySite'
SAMPLE_DATA_BY_COUNTY = 'sampleData/byCounty'
SAMPLE_DATA_BY_STATE = 'sampleData/byState'
SAMPLE_DATA_BY_BOX = 'sampleData/byBox'
SAMPLE_DATA_BY_CBSA = 'sampleData/byCBSA'

LIST_STATES = 'list/states'
LIST_COUNTIES_BY_STATE = 'list/countiesByState'
LIST_SITES_BY_COUNTY = 'list/sitesByCounty'
LIST_CBSAs = 'list/cbsas'
LIST_PARAM_CLASSES = 'list/classes'
LIST_PARAM_IN_CLASS = 'list/parametersByClass'

class DataFetcher():
    """
    Python API to queury from AQD data API
    """

    def __init__(self):
        self.params = {
            'email': EMAIL,
            'key': KEY}
        self.all_codes = self.get_codes('list/parametersByClass', all=True, nparams={'pc':'ALL'})
        self.all_codes = pd.DataFrame(self.all_codes).set_index('code')
        self.processor = Processor()
        vocs = self.get_codes(LIST_PARAM_IN_CLASS, all=True, nparams={'pc':'PAMS_VOC'})
        self.vocs = [i['value_represented'] for i in vocs]
        
    def get_codes(self, filter_url, all: bool, value=None, nparams=None):
        """
        Search for codes for a particular filter. Either show all results or search 
        for specific value.
        """
        # Try to get code from the all_codes if possible:
        params = self.params.copy()
        if nparams:
            params.update(nparams)
        r = requests.get(url=URL+filter_url, params=params)
        data = r.json()['Data']
        if all:
            return data
        else:
            search = [item for item in data if item['value_represented'] == value][0]
            return search['code']
    
    def get_data(self, data_url, param, bdate, edate, df=False, nparams=None):
        params = self.params.copy()
        params['param'] = param
        params['bdate'] = bdate
        params['edate'] = edate
        if params:
            params.update(nparams)
        r = requests.get(url=URL+data_url, params=params)

        try:
            data = r.json()['Data']
            if df:
                return pd.DataFrame(data)
            return data
        except:
            print(r.json())
    
    def find_code(self, value, verbose=False):
        # Look for code in self.all_codes
        try:
            code = self.all_codes.loc[self.all_codes['value_represented'] == value].index[0]
            if verbose:
                print(f"{value} code is: {code}")
            return code
        except Exception as e:
            print(f"Could not find {value}.")
            # print(e)
    
    def create_dataset(self, bdate, edate, site=None, county=None, state=None, processed=True, verbose=False, vocs=False):
        code_names = [*CRITERIA_POLLUTANTS, *MET_VARS]
        if vocs:
            voc_code_names = [self.all_codes.loc[code]['value_represented'] for code in self.voc_codes]
            code_names += voc_code_names
        
        codes = [self.find_code(v) for v in code_names]
        dct = {codes[i]: code_names[i] for i in range(len(codes))}

        dfs = []
        if state:
            if county:
                if site:
                    for code in codes:
                        if verbose:
                            print(f"\n Fetching data for {dct[code]}...", end="\n\n")
                        
                        df = self.get_data(SAMPLE_DATA_BY_SITE, code, bdate, edate, df=True, nparams={'state':state, 'county':county, 'site': site})

                        if df.empty:
                            print(f"No data for {dct[code]}")
                            continue
                        
                        if processed:
                            df = self.processor.process(df, dct[code])

                        dfs.append(df)

            # TODO: rest of logic for non-site

        else:
            raise Exception("Please enter state/county/site codes.")
        
        return self.processor.join(dfs)
    
    def find_best_location(self, state='06', county='037', bdate=20000101, edate=20210101):
        """
        Go through all sites in los angeles county and find site with the most dfs
        """
        print(f"Searching county {county} in state {state}...", end=" ")
        sites = self.get_codes(LIST_SITES_BY_COUNTY, all=True, nparams={'state':state, 'county':county})
        sites = [(site['code'], site['value_represented']) for site in sites if site['value_represented']]
        print(f"Found {len(sites)} sites.")

        codes = [self.find_code(v) for v in [*CRITERIA_POLLUTANTS , *MET_VARS, *PAMS]]
        sample_days = [self.sample_day_in_year(year, year + 10000) for year in range(bdate, edate, 50000)]
        # sample_days = [(i, i+1130) for i in range(20000101, 20210101, 50000)]
        res = {}
        res['Data'] = {}
        res['Metadata'] = {'dates':sample_days, 'codes':codes}
        for site, name in sites:
            res['Data'][name] = []
            for code in codes:
                year_res = [self.find_data_availability(site, county, state, code, bdate, edate) for bdate, edate in sample_days]
                res['Data'][name].append(year_res)
            print(f"Finished site {site}, {name}")
        
        return res
    
    def find_data_availability(self, site, county, state, code, bdate, edate):
        try:
            df = self.get_data(SAMPLE_DATA_BY_SITE, code, bdate, edate, df = True, nparams={'state':state, 'county':county, 'site': site})
            return not (df.empty)
        except:
            return -1
    
    def find_voc_availability(self, sites, sites_codes, dates, state='06', county='037'):
        codes = [r['code'] for r in self.get_codes(LIST_PARAM_IN_CLASS, all=True, nparams={'pc':'PAMS_VOC'})]
        self.voc_codes = codes 

        res = {}
        res['Data'] = {}
        res['Metadata'] = {'dates':dates, 'codes':codes}
        for name, site, site_dates in zip(sites, sites_codes, dates):
            res['Data'][name] = []
            for code in codes:
                year_res = [self.find_data_availability(site, county, state, code, site_date[0], site_date[1]) for site_date in site_dates]
                res['Data'][name].append(year_res)
            print(f"Finished site {site}, {name}")
        
        return res
    
    def sample_day_in_year(self, bdate, edate):
        # Sample random day in every year
        sample_date = random.choice(pd.date_range(start=str(bdate), end=str(edate)))
        return sample_date.date().strftime("%Y%m%d"), (sample_date.date() + datetime.timedelta(1)).strftime("%Y%m%d")


### =========================VARIABLES============================== ###

# NOTE: Do I have the correct wind variable?
# NOTE: Mixing speed?
# NOTE: Types of radiation?
# NOTE: Barometric or ambient pressure?

# CRITERIA_POLLUTANTS = ["Carbon monoxide", "Sulfur dioxide", "Nitrogen dioxide (NO2)", "Ozone", "PM2.5 - Local Conditions"]

CRITERIA_POLLUTANTS = ["Carbon monoxide", "Nitrogen dioxide (NO2)", "Ozone", "PM2.5 - Local Conditions"]
PAMS = ["Nitric oxide (NO)", "Oxides of nitrogen (NOx)"]
MET_VARS = ["Wind Direction - Resultant", "Wind Speed - Resultant", "Outdoor Temperature", "Relative Humidity ", "Solar radiation", "Ultraviolet radiation", "Barometric pressure"] 
# NOTE: Excluded  "Mixing Height" and rain