# CHEM150 Atmospheric Chemistry ML Modelling
## Author: Thomas Cintra

This is my lab github repo :) 

Please note that I am going to use a virtual environment to manage any modules used for the models and data processing. If you encounter problems run the following commands:

'''
$ python3 -m venv venv # Creates a virtual environment
$ source venv/bin/activate # Activates virtual environment
$ python3 -m pip install --upgrade pip
$ python3 -m pip install -r requirements.txt # Download requirements
'''

For now, this repository:

<ul>
    <li>Fetches data from AQS using a python API.</li>
    <li>Provides some logic to fetch relevant air pollutant, ozone, particulate matter, VOC, and metereological data into separate datasets for local handling.</li>
    <li>Some plotting!</li>
</li>
