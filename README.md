# CHEM150 Atmospheric Chemistry ML Modelling
## Author: Thomas Cintra

This is my lab github repo :) 

Please note that I am going to use a virtual environment to manage any modules used for the models and data processing. If you encounter problems run the following commands:

```
$ python3 -m venv venv # Creates a virtual environment
$ source venv/bin/activate # Activates virtual environment
$ python3 -m pip install --upgrade pip
$ python3 -m pip install -r requirements.txt # Download requirements
```

For now, this repository:

<ul>
    <li>Fetches data from AQS using a python API.</li>
    <li>Provides some logic to fetch relevant air pollutant, ozone, particulate matter, VOC, and metereological data into separate datasets for local handling.</li>
    <li>Some plotting!</li>
</li>

Finding the best site:
We can't realistically get data for an entire year, for every site, for every code, for multiple years. If we want to have an idea of what critical data was available over the span of decades, we need to do some sampling. As a first pass we sample 1 random day every 5 years starting in 2000. Then we get the top 5 sites with the most critical data for a given 5 year period, which happens to be Los Angeles-North Main Street no matter what data range we pick. We don't include VOCs yet as the MET and CRITERIA data are much more crucial, two of them being our target variables. 

From the top 5 we then rank them based on the availability of PAMS_VOC data. We only need to check the date that resulted in the most available data from the previous queury.

Step (1) takes about 30 minutes to run on my machine, could be faster using multiprocessing or using google collab resources?
Step (2) takes about 20 minutes to run.