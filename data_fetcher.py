import codecs
import requests
import pandas as pd

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
    
    def create_dataset(self, bdate, edate, site=None, county=None, state=None, processed=True, verbose=False):
        codes = [self.find_code(v) for v in [*CRITERIA_POLLUTANTS, *MET_VARS]]
        dct = {codes[i]: [*CRITERIA_POLLUTANTS, *MET_VARS][i] for i in range(len(codes))}
        
        # NOTE: Not doing VOCs yet
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
    
    def find_best_location(self, state='06', county='037', bdate=20180101, edate=20180102):
        """
        Go through all sites in los angeles county and find site with the most dfs
        """
        print(f"Searching county {county} in state {state}...", end=" ")
        
        sites = self.get_codes(LIST_SITES_BY_COUNTY, all=True, nparams={'state':state, 'county':county})
        sites = [(site['code'], site['value_represented']) for site in sites if site['value_represented']]
        
        print(f"Found {len(sites)} sites.")

        codes = [self.find_code(v) for v in [*CRITERIA_POLLUTANTS, *MET_VARS]]

        res = {}
        for site, name in sites:
            res[name] = []
            for code in codes:
                try:
                    df = self.get_data(SAMPLE_DATA_BY_SITE, code, bdate, edate, df = True, nparams={'state':state, 'county':county, 'site': site})

                    if df.empty:
                        res[name].append(0)
                    else:
                        res[name].append(1)
                except:
                    res[name].append(-1)
        
        return res


### =========================VARIABLES============================== ###

# NOTE: Do I have the correct wind variable?
# NOTE: Mixing speed?
# NOTE: Types of radiation?
# NOTE: Barometric or ambient pressure?

# CRITERIA_POLLUTANTS = ["Carbon monoxide", "Sulfur dioxide", "Nitrogen dioxide (NO2)", "Ozone", "PM2.5 - Local Conditions"]

CRITERIA_POLLUTANTS = ["Carbon monoxide", "Nitrogen dioxide (NO2)", "Ozone", "PM2.5 - Local Conditions"]


MET_VARS = ["Wind Direction - Resultant", "Mixing Height", "Outdoor Temperature", "Relative Humidity ", "Solar radiation", "Ultraviolet radiation", "Barometric pressure", "Rain/melt precipitation"] 
