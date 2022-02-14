import requests
import pandas as pd

EMAIL = "tcintra@hmc.edu" # Should transition to env
KEY = 'russetwren13'

URL = 'https://aqs.epa.gov/data/api/'

class DataFetcher():
    """
    Python API to queury from AQD data API
    """

    def __init__(self):
        self.params = {
            'email': EMAIL,
            'key': KEY}
        
    def get_codes(self, filter_url, all: bool, value=None, nparams=None):
        """
        Search for codes for a particular filter. Either show all results or search 
        for specific value.
        """
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
        data = r.json()['Data']
        if df:
            return pd.DataFrame(data)
        return data
    