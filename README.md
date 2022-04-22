# CHEM150 Atmospheric Chemistry ML Modelling
## Author: Thomas Cintra

This is my lab github repo :) 

# Outline

Below we enumerate what is currently in this repository.

<ul>
    <li>Defines a Python API to fetch AQS data (```datafetcher.py```).</li>
    <li>Provides a sample notebook to determine the best site to sample from in Los Angeles County (```lab_notebook.ipynb```).</li>
    <li>Provides a sample notebook to fetch relevant AQS data (```lab_notebook.ipynb```).</li>
    <li>Provides a sample notebook to explore relevant CEDS emissions data (```hemco_data_exploration.ipynb```).</li>
    <li>Provides a python script to generate a 2018 dataset for LA North Main St (```generate.py```), including AQS and CEDS data.</li>
    <li>Provides a sample notebook to run a Random Forest model on the above dataset (```lab_notebook_2.ipynb```).</li>
</li>

## Setup

Please note that I use a virtual environment to manage any modules used for the models and data processing. To begin using this repo use the following commands on the root of this directory:

```
$ python3 -m venv venv # Creates a virtual environment
$ source venv/bin/activate # Activates virtual environment
$ python3 -m pip install --upgrade pip
$ python3 -m pip install -r requirements.txt # Download requirements
```

You must also create a ```.env``` file and populate it with your email and password to the AQS api. Your .env file should look like:

```
EMAIL="example@example.com"
KEY="example"
```

### Using DataFetcher
Please refer to ```lab_notebook.ipynb``` for examples on how to use the DataFetcher class. It has 3 primary purposes: (1) Finding the site with the most data in a particular county/state; (2) fetching AQS data; and (3) fetching CEDS data. Important functions have detailed docstrings.

### Finding the best site:
We can't realistically get data for an entire year, for every site, for every code, for multiple years. If we want to have an idea of what critical data was available over the span of decades, we need to do some sampling. As a first pass we sample 1 random day every 5 years starting in 2000. Then we get the top 5 sites with the most critical data for a given 5 year period, which happens to be Los Angeles-North Main Street no matter what data range we pick.

From the top 5 we then rank them based on the availability of PAMS_VOC data. We only need to check the date that resulted in the most available data from the previous queury.

However, we want to eventually find more relevant sites to train on so we could replicate the above logic to find the best sites accross multiple states, etc. Even better, we could find a clever way to aggregate data accross neighbouring sites.

### Building a dataset

Running the ```generate.py``` script will create 3 datasets in the ```data/clean/Los_Angeles-North_Main_Street/2018``` directory (the structure is ```data/clean/\<site\>/\<year\>```). The core dataset contains CRITERIA and MET data, the vocs dataset contains VOCs data, and the emissions dataset contains CEDS data. Use the following command:

```
$ python3 generate.py
```