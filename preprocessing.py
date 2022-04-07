import pandas as pd
import numpy as np

class Processor():
    """
    Class to preprocess AQS data in specified format to feed into models.
    """
    
    def __init__(self):
        pass

    def project_unique(self, df, measurement, verbose=False):
        """
        Keep only columns that have 2 of more unique values.
        """
        cols_dict = {col: df[col].nunique() for col in df.columns}
        all_cols = {k: v for k,v in cols_dict.items() if v <= 1}
        kept_cols = {k: v for k,v in cols_dict.items() if v > 1}
        
        # Keep only variables we care about (changing) 
        df = df[kept_cols.keys()].copy()
        df['datetime'] = pd.to_datetime(df['date_local'] + ' ' + df['time_local'])
        df.set_index('datetime', inplace=True)
        df = df.drop(['date_gmt', 'time_gmt', 'date_local', 'time_local'], axis=1)

        # NOTE: Should I drop this?
        if 'date_of_last_change' in df.columns:
            df = df.drop(['date_of_last_change'], axis=1)

        if verbose:
            print('Kept the following columns:')
            print(df.columns)
            print()
            print('Removed the following columns:')
            print([col for col in all_cols if col not in df.columns])
            print()

        df = df.rename({'sample_measurement': measurement}, axis=1)

        return df
    
    def process(self, df, measurement, change_freq=False, select_method=False, drop_lat_lon=True, remove_duplicates=False):
        if select_method:
            df = df.loc[df['method'] == df['method'].unique()[0]].copy()
        df['datetime'] = pd.to_datetime(df['date_local'] + ' ' + df['time_local'])
        df = df[['datetime', 'sample_measurement', 'latitude', 'longitude']]
        df = df.rename({'sample_measurement': measurement}, axis=1)

        # TODO: Fix this, currently just select the first year period to avoid duplicate index, but this might select the wrong data
        duplicates = df.duplicated(subset='datetime', keep='first')
        duplicates = np.where(duplicates)[0]
        if len(duplicates) > 0:
            df = df.iloc[:duplicates[0]]
        
        df.set_index(['datetime'], inplace=True)

        if change_freq: 
            print(df.head())
            df = df.asfreq('1h', method='ffill')
        if drop_lat_lon:
            df = df.drop(['latitude', 'longitude'], axis=1)

        return df
        
    def join(self, dfs):
        df = dfs[0].join(dfs[1:], how='outer')
        df = df.drop([x for x in df.columns if (('latitude' in x) and (x != 'latitude'))], axis=1)
        df = df.drop([x for x in df.columns if (('longitude' in x) and (x != 'longitude'))], axis=1)
        df = df.resample('1h').mean()
        return df