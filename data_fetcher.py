import requests
import pandas as pd
import random
import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
import netCDF4 as nc
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv

from preprocessing import Processor

# Sample env vars:
# EMAIL="example@example.com"
# KEY="example"

load_dotenv()

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

CEDS_AQS_MAP = {
    'ALD2' : {'include' : True, 'matches' : ['Acetaldehyde'], 'notes':'not lumped'},
    'ALK4_butanes' : {'include' : True, 'matches' : ['2,2-Dimethylbutane', '2,3-Dimethylbutane', 'Isobutane', 'n-Butane', '2,2,3-Trimethylbutane'], 'notes' : 'lumped'}, 
    'ALK4_hexanes' : {'include' : True, 'matches' : ['n-Hexane','Cyclohexane', '3-Methylhexane','Methylcyclohexane','2-Methylhexane','2,4-Dimethylhexane','2,3-Dimethylhexane','3-Ethylhexane','Ethylcyclohexane','2-Methylhexane & cyclohexane','2,2,4-Trimethylhexane','2,5-Dimethylhexane'],  'notes' : 'lumped'},
    'ALK4_pentanes' : {'include' : True, 'matches' : ['n-Pentane','Isopentane','3-Methylpentane','Cyclopentane','2,2,4-Trimethylpentane','2,3,4-Trimethylpentane','Methylcyclopentane','2-Methylpentane','2,3-Dimethylpentane','2-2-3-Trimethylpentane','Isopentane & cyclopentane','Methylcyclopentane & 2,4-dimethylpentane','cis-1,2-Dimethylcyclopentane','trans-1,3-Dimethylcyclopentane', '2-Methylheptane', '2-Methylheptane & 3-Methylheptane', 'n-Heptane', '3-Methylheptane', 'Heptane','2,2-Dimethylheptane','4-Methylheptane', 'n-Octane', 'n-Nonane','Isomers of dodecane'], 'notes' : 'lumped'},
    'BC' : {'include' : True, 'matches' : ['Black carbon PM2.5 STP', 'Black Carbon PM2.5 Corrected', 'Black Carbon PM10 LC'], 'notes' : 'Black Carbon (aerosol)'},
    'BENZ' : {'include' : True, 'matches' : ['Benzene'], 'notes' : 'not lumped.'},
    'BUTENE' : {'include' : True, 'matches' : ['1-Butene', 'cis-2-Butene', 'trans-2-Butene', '1-Pentene','trans-2-Pentene,cis-2-Pentene','4-Methyl-1-pentene','2-Methyl-2-pentene','2,3-Dimethyl-2-pentene','2-Methyl-1-pentene','2,4,4-Trimethyl-1-pentene','2,4,4-Trimethyl-2-pentene','Cyclopentene','cis-4-Methyl-2-pentene','3-Methyl-1-butene & cyclopentene','2-Methyl-2-butene & 1-pentene','4-Methylpentene & 3-methylpentene','3-Methyl-1-butene & Cyclopentene','1-Hexene & 2-Methyl-1-pentene'], 'notes' : 'These stand for other_alkenes_and_alkynes <- super weird category, sometimes also called "isomers of pentene".'},
    'C2H2' : {'include' : True, 'matches' : ['Acetylene'], 'notes' : 'not lumped'},
    'C2H4' : {'include' : True, 'matches' : ['Ethylene'], 'notes' : 'not lumped'},
    'C2H6' : {'include' : True, 'matches' : ['Ethane'], 'notes' : 'not lumped'},
    'C3H8' : {'include' : True, 'matches' : ['Propane'], 'notes' : 'not lumped'},
    'CH2O' : {'include' : True, 'matches' : ['Formaldehyde'], 'notes' : 'not lumped'},
    'CHC' : {'include' : True, 'matches' : [], 'notes' : 'lumped. There are a bunch, but we dn not need them. Some names are “obvious” like 1,1,1-Trichloro-2,2-bis (p-chlorophenyl) ethane but others are pesticides with chemical company names like Endrin'},
    'CO' : {'include' : True, 'matches' : ['CO'],'notes' : ''},
    'CO2' : {'include' : False, 'matches' : [], 'notes' : ''},
    'EOH' : {'include' : False, 'matches' : [], 'notes' : 'not lumped (ethanol)'},
    'ESTERS' : {'include' : True, 'matches' : ['n-Propyl acetate', 'Ethyl acrylate', 'n-Butyl acrylate', 'Methyl methacrylate', 'Vinyl acetate', 'Butyl acetate'], 'notes' : 'lumped'},
    'ETHERS' : {'include' : False, 'matches' : [], 'notes' :'probably can just ignore these'},
    'HCOOH' : {'include' : False, 'matches' : [], 'notes' : 'Does not look like it is in the EPA dataset'},
    'MEK' : {'include' : True, 'matches' : ['Methyl ethyl ketone & methacrolein', 'Methyl ethyl ketone', 'Methacrolein'], 'notes' : 'MEK and Methacrolein are usually lumped together - same mass so measured as one often'},
    'N2O' : {'include' : False, 'matches' : [], 'notes' : 'It is code 42605 - we can skip it'},
    'NH3' : {'include' : True, 'matches' : ['Ammonia'], 'notes' : 'only 42604.'},
    'NO' : {'include' : True, 'matches' : ['Nitric oxide (NO)'], 'notes' : 'I am not sure if any of these are nitric oxide.'},
    'OC' : {'include' : True, 'matches' : ['Organic carbon PM10 STP', 'Organic Carbon Mass PM2.5 LC'], 'notes' : 'Organic Carbon, meaning organic aerosol.'},
    'OTHER_AROM' : {'include' : False, 'matches' : [], 'notes': 'pretty much everything else that ends with “benzene”, “toluene”,or “xylene” that is not included in BENZ, TOLU, XYLE, and TMB goes here. We can skip them though'},
    'OTHER_VOC' : {'include' : False, 'matches' : [], 'notes' : 'many of the AQS ones could, but anything relegated to “other” takes part in almost no interesting chemistry, so we can skip them'},
    'PRPE' : {'include' : True, 'matches' : ['Propylene'], 'notes' : ''},
    'SO2' : {'include' : True, 'matches' : ['Sulfur dioxide', 'SO2 max 5-min avg'], 'notes' : ''},
    'TMB' : {'include' : True, 'matches' : ['1,2,3-Trimethylbenzene', '1,2,4-Trimethylbenzene', '1,3,5-Trimethylbenzene'], 'notes' : ''},
    'TOLU' : {'include' : True, 'matches' : ['Toluene'], 'notes' : 'not lumped'},
    'XYLE' : {'include' : True, 'matches' : ['m/p Xylene','m-Xylene', 'o-Xylene','p-Xylene','Xylene(s)'], 'notes' : ''}
}

class DataFetcher():
    """
    Python API to queury from AQS database.
    """

    def __init__(self):
        # params define the access tokens to query AQS database
        self.params = {
            'email': os.getenv("EMAIL"),
            'key': os.getenv("KEY")}
        self.all_codes = self.get_codes('list/parametersByClass', all=True, nparams={'pc':'ALL'})
        self.all_codes = pd.DataFrame(self.all_codes).set_index('code')
        self.processor = Processor()
        vocs = self.get_codes(LIST_PARAM_IN_CLASS, all=True, nparams={'pc':'PAMS_VOC'})
        self.vocs = [i['value_represented'] for i in vocs]
        
    def get_codes(self, filter_url, all: bool, value=None, nparams=None):
        """
        Search for codes for a particular filter. Either show all results or search 
        for specific value.

        Parameters:
            filter_url: String - Endpoint of AQS query. Example: 'list/states'
            all: bool - Whether to return all codes for this endpoint or filter for some value
            value: String - Value to filter by
            nparams: dict - Required parameters for some AQS queries
        
        Returns:
            HTTP Response Data: json or pd.DataFrame

        Example: 
        
        >>> DataFetcher().get_codes(LIST_PARAM_IN_CLASS, all=False, value='Carbon monoxide', nparams={'pc':'CRITERIA'})
        42101
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
        """
        Queries AQS for data from data_url

        Parameters:
            data_url: String - Endpoint of AQS query. Example: 'sampleData/bySite'.
            param: String - Parameter to query
            bdate: int - First data entry time.
            edate: int - Last data entry time.
            df: bool - Whether to return output as dataframe.
            nparams: dict - Required parameters for some AQS queries
        
        Returns:
            HTTP Response Data: json or pd.DataFrame

        Example: 
        
        DataFetcher().get_data(SAMPLE_DATA_BY_STATE, 42101, 20180101, 20181231, df=True, nparams={'state':06})
        """
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
        """
        Find code for a particular value (eg. 'Ozone')

        Parameters:
            value: String - Value to search for.
        
        Returns:
            code: int - The code you are searching for.
        """
        # Look for code in self.all_codes
        try:
            code = self.all_codes.loc[self.all_codes['value_represented'] == value].index[0]
            if verbose:
                print(f"{value} code is: {code}")
            return code
        except Exception as e:
            print(f"Could not find {value}.")
            # print(e)
    
    def find_name(self, code):
        """
        Inverse of find_code(...)
        """
        # Look for code in self.all_codes
        try:
            code = self.all_codes.loc[code].value_represented
            return code
        except Exception as e:
            print(f"Could not find {code}.")
            # print(e)
    
    def create_dataset(self, bdate, edate, site=None, county=None, state=None, processed=True, verbose=False):
        """
        Generates core dataset (CRITERIA pollutants and MET vars).

        Parameters:
            bdate: int - First data entry time.
            edate: int - Last data entry time.
            site: String - Site code.
            count: String - County code.
            state: String - State code.
            processed: True - Whether to run dataset through processor class.
        
        Returns:
            HTTP Response Data: json or pd.DataFrame

        Example: 
        
        DataFetcher().create_dataset(20200101, 20200102, site='1103', county='037', state='06', processed=True, verbose=False)
        """
        code_names = [*CRITERIA_POLLUTANTS, *MET_VARS]
        
        codes = [self.find_code(v) for v in code_names]
        dct = {codes[i]: code_names[i] for i in range(len(codes))}

        dfs = []
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

        return self.processor.join(dfs)
    
    def find_best_location(self, state='06', county='037', bdate=20000101, edate=20210101):
        """
        Go through all sites in county and find site with the most data

        Parameters:
            bdate: int - First data entry time.
            edate: int - Last data entry time.
            site: String - Site code.
            county: String - County code.
        
        Returns:
            dict - Output of search.
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
        """
        Helper function for find_best_location()
        """
        try:
            df = self.get_data(SAMPLE_DATA_BY_SITE, code, bdate, edate, df = True, nparams={'state':state, 'county':county, 'site': site})
            return not (df.empty)
        except:
            return -1
    
    def find_voc_availability(self, sites, sites_codes, dates, state='06', county='037'):
        """
        Go through all sites in county and find site with the most VOC data

        Please refer to lab_notebook.ipynb for example usage.
        """
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
        """
        Helper function.
        """
        # Sample random day in every year
        sample_date = random.choice(pd.date_range(start=str(bdate), end=str(edate)))
        return sample_date.date().strftime("%Y%m%d"), (sample_date.date() + datetime.timedelta(1)).strftime("%Y%m%d")

    def get_voc_data(self, bdate, edate, state, county, site, vocs):
        """
        Get dataset for VOCs

        Parameters:
            bdate: int - First data entry time.
            edate: int - Last data entry time.
            site: String - Site code.
            county: String - County code.
            state: String - State code.
        
        Returns:
            pandas DataFrame.
        """
        dfs = []
        for voc in vocs:
            code = self.find_code(voc)
            df = self.get_data(SAMPLE_DATA_BY_SITE, code, bdate, edate, df=True, nparams={'state':state, 'county':county, 'site': site})

            if df.empty:
                print(f"No data for {voc}")
                continue

            df = self.processor.process(df, voc, change_freq=False, select_method=True, drop_lat_lon=True, remove_duplicates=True)
            dfs.append(df)
        
        return self.processor.join(dfs)

    
    ### CEDS DATA ###

    # Get all URLS
    def get_ceds_links(self, year='2018'):
        """
        Web-scraping tool to get the links to all CEDS datasets.

        Parameters:
            year: String - Year to get data for.
        
        Returns:
            Tuple([String], String) - Links to query from CEDS database and year url endpoint.
        """
        url = 'http://ftp.as.harvard.edu/gcgrid/data/ExtData/HEMCO/CEDS/v2021-06/' + year + '/'
        self.ceds_url = url
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for link in soup.findAll('a'):
            links.append(link.get('href'))
        nc_links = links[5:]
        self.nc_links = nc_links
        self.ceds_compounds = {}
        return nc_links, url
    
    def save_ceds_ncs(self):
        """
        Query the CEDS database for the emissions data and write it locally.
        NOTE: This must run before any datasets are created for CEDS.
        """
        if self.nc_links:
            for endpoint in self.nc_links:
                r = requests.get(self.ceds_url + endpoint)
                open('./data/2018/' + endpoint, 'wb').write(r.content)

    def get_compound_df(self, path, site_lat, site_lon, endpoint):
        """
        Helper function for make_ceds_df. Converts one CEDS netcdf file to a pandas df.
        """
        ds = nc.Dataset(path, format="NETCDF4")
        lat_idx = np.where(ds.variables['lat'][:] == site_lat)
        lon_idx = np.where(ds.variables['lon'][:] == site_lon)

        self.ceds_compounds[endpoint.replace('-em-anthro_CMIP_CEDS_2018.nc', '')] = endpoint
        
        data = []
        for var in ds.variables:
            if var not in ['time', 'lat', 'lon']:
                data.append(ds.variables[var][:][:, lat_idx, lon_idx].flatten())
        
        data = np.asarray(data).T
        df = pd.DataFrame(data, columns = [x for x in ds.variables if x not in ['time', 'lat', 'lon']])
        df.index = ds.variables['time'][:]
        return df

    def make_ceds_df(self, lat, lon, nc_links):
        """
        Make dataframe with CEDS emissions.

        Parameters:
            lat: int - Latitude of relevant site.
            lon: int - Longitude of relevant site.
            nc_links: [String] - Endpoints of emissions data to query.
        
        Returns:
            pandas DataFrame with CEDS emissions.
        """
        dfs = []
        for endpoint in nc_links:
            df = self.get_compound_df('./data/2018/' + endpoint, lat, lon, endpoint)
            dfs.append(df)

        full_df = dfs[0].join(dfs[1:], how='outer')

        # NOTE: Not sure how to convert to timestamp so I will just convert to the first of the month for the given year
        start = datetime.datetime(2018, 1, 1, 0, 0)
        dates = [start + relativedelta(months=i) for i in range(0, 12)]
        full_df['datetime'] = dates
        full_df.index = full_df['datetime']
        full_df = full_df.drop(['datetime'], axis=1)
        full_df.loc[datetime.datetime(2018, 12, 31, 23, 0)] = full_df.loc[datetime.datetime(2018, 12, 1)] # Repeat last row
        full_df = full_df.asfreq(freq='1h', method='ffill')

        return full_df
    
    def aggregate_ceds_data(self, df):
        """
        Aggregates data for different sectors for each compound so we only have one column per compound.
        """
        ndf = df.copy()
        for compound in self.ceds_compounds:
            cols = [col for col in df.columns if (compound + '_' in col) and (col.startswith(compound))]
            if len(cols) != 8:
                raise("Not properly aggregating columns.")
            compound_aggregated = df[cols].sum(axis=1)
            ndf = ndf.drop(cols, axis=1)
            ndf[compound] = compound_aggregated
        return ndf
    
    def get_ceds_data(self, year, lat=34.25, lon=-118.25, keep=[]):
        """
        Get aggregated CEDS data for all compounds in keep 
        """
        nc_links, _ = self.get_ceds_links(year=year)
        nc_links = [link for link in nc_links if link.replace('-em-anthro_CMIP_CEDS_2018.nc', '') in keep]
        ceds_df = self.make_ceds_df(lat, lon, nc_links)
        return self.aggregate_ceds_data(ceds_df)
    
    ### MISC ###
    
    def get_final_compounds(self):
        """
        Get VOCs that have emissions in CEDS data and vice versa. Basically a set intersection.
        """
        with open('voc_data.json', 'r') as f:
            voc_r = json.load(f)
        vocs = sorted([self.find_name(code) for code in voc_r['Metadata']['codes']])
        # Get all vocs in AQS that have emissions recorded by CEDS and
        matched_vocs = set()
        for k in CEDS_AQS_MAP:
            for match in CEDS_AQS_MAP[k]['matches']:
                matched_vocs.add(match)
        final_vocs = [x for x in vocs if x in matched_vocs]
        # Get all emissions recorded by CEDS that are used by a VOC in AQS data
        final_emissions = [k for k in CEDS_AQS_MAP if len(set(CEDS_AQS_MAP[k]['matches']) & set(final_vocs)) != 0]

        return final_vocs, final_emissions

### =========================VARIABLES============================== ###

CRITERIA_POLLUTANTS = ["Carbon monoxide", "Nitrogen dioxide (NO2)", "Ozone", "PM2.5 - Local Conditions"]
PAMS = ["Nitric oxide (NO)", "Oxides of nitrogen (NOx)"]
MET_VARS = ["Wind Direction - Resultant", "Wind Speed - Resultant", "Outdoor Temperature", "Relative Humidity ", "Solar radiation", "Ultraviolet radiation", "Barometric pressure"] 