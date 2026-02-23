## 0.1 Load Packages ############################

# !pip install requests python-dotenv  # run this once in your environment

import json
import os  # for reading environment variables
import requests  # for making HTTP requests
from dotenv import load_dotenv  # for loading variables from .env

## 0.2 Load Environment Variables ################

# Load environment variables from the .env file in the project root
# This matches the behavior of readRenviron(".env") in 02_example.R
load_dotenv(".env")

# Get the API key from the environment
X_API_Key = os.getenv("X-API-Key")

## 1. API Documentation ############################
# https://docs.openaq.org/   # documentation for the OpenAQ API
# Name: OpenAQ Air Quality API
# Description: Open air quality data, with worldwide coverage.
# Base URL: https://api.openaq.org/v3
# Authentication: API key in the header
# Endpoints:
# - https://api.openaq.org/v3/locations?iso=HK
# - https://api.openaq.org/v3/sensors/22471/days/monthly

## 2. Make API Request on locations in Hong Kong ###########################

# Plan: Get monitor stations and sensor IDs in the locations in Hong Kong
# Execute query and save response as object
HK_locations = requests.get(
    "https://api.openaq.org/v3/locations?iso=HK",
    headers={"x-api-key": X_API_Key},
)

## 2.1. Inspect Response ###########################
# View response status code (200 = success)
print(HK_locations.status_code)

## 3. Make API Request on sensor ID 22471 at Tung Chung Station ID 7727 ###########################

# look up sensor ID for Tung Chung monitor station and PM2.5 sensor ID
# Tung Chung Station ID: 7727 PM2.5 sensor ID: 22471

# Find the daily averages for sensor ID 22471 at Tung Chung Station ID 7727
# Set parameters for date range 2020-01-01 to 2025-12-31 (2025)
# Define your parameters in a dictionary
params = {
    "date_from": "2020-01-01T00:00:00",
    "date_to": "2025-12-31T23:59:59"
}
# New Territories:Tung Chung Station ID: 7727 PM2.5 sensor ID: 22471
TC_monthly_averages = requests.get(
    "https://api.openaq.org/v3/sensors/22471/days/monthly",
    headers={"x-api-key": X_API_Key},
    params=params,
)

# Kowloon: Mong Kok Station ID: 7728 PM2.5 sensor ID: 22477
MK_monthly_averages = requests.get(
    "https://api.openaq.org/v3/sensors/22477/days/monthly",
    headers={"x-api-key": X_API_Key},
    params=params,
)

# Hong Kong Island:Central & Western: Western District Station ID: 7730 PM2.5 sensor ID: 22481
CW_monthly_averages = requests.get(
    "https://api.openaq.org/v3/sensors/22481/days/monthly",
    headers={"x-api-key": X_API_Key},
    params=params,
)

# Hong Kong Island: Causeway Bay: Causeway Bay Station ID: 7732 PM2.5 sensor ID: 22492
CB_monthly_averages = requests.get(
    "https://api.openaq.org/v3/sensors/22492/days/monthly",
    headers={"x-api-key": X_API_Key},
    params=params,
)


## 3.1. Inspect Response ###########################
# View response status code (200 = success)
print(TC_monthly_averages.status_code)
print(MK_monthly_averages.status_code)
print(CW_monthly_averages.status_code)
print(CB_monthly_averages.status_code)
# Number of records returned : 60 (60 months in 2020-2025)

## 3.2. Save all monthly_averages to JSON file (overwrite) ###########################
monthly_averages_data = {
    "TC_monthly_averages": TC_monthly_averages.json() if TC_monthly_averages.status_code == 200 else {"error": TC_monthly_averages.status_code},
    "MK_monthly_averages": MK_monthly_averages.json() if MK_monthly_averages.status_code == 200 else {"error": MK_monthly_averages.status_code},
    "CW_monthly_averages": CW_monthly_averages.json() if CW_monthly_averages.status_code == 200 else {"error": CW_monthly_averages.status_code},
    "CB_monthly_averages": CB_monthly_averages.json() if CB_monthly_averages.status_code == 200 else {"error": CB_monthly_averages.status_code},
}
out_path = os.path.join(os.path.dirname(__file__), "monthly_averages.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(monthly_averages_data, f, indent=2)
print(f"Saved {out_path} (overwrite)")

# Clear environment
globals().clear()