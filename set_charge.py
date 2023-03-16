#!/usr/bin/env python3

import datetime
import os
from givenergy_modbus.client import GivEnergyClient
from givenergy_modbus.model.plant import Plant
from pysolcast.rooftop import RooftopSite
import json
from os.path import exists

# Solcast give limited free API calls, so cache the data for testing
cache_file = 'forcast-cache.json'
if os.path.exists(cache_file):
    print("Using cached forcast data")
    with open('forcast-cache.json') as cache_file:
        file_contents = cache_file.read()
    forecasts = json.loads(file_contents)
else:
    print("Getting forcast data from solcast")
    # Get forcast from solcast for next day
    site = RooftopSite(os.environ["SOLCAST_API_KEY"],
                       os.environ["SOLCAST_RESOURCE_ID"])
    forecasts = site.get_forecasts()
    json_str = json.dumps(forecasts, indent=4)
    with open('forcast-cache.json', 'w') as cache_file:
        json.dump(forecasts, cache_file, indent=4)


# Update overnight change percentage based on forecast
# ... Let's do some bad maths....
battery_capacity_watt_hours = 9500

client = GivEnergyClient(host=os.environ["INVERTOR_IP_1"])


# Set data
client.set_battery_target_soc(85)
# client.set_charge_slot_1((datetime.time(hour=0, minute=30), datetime.time(hour=4, minute=00)))
# # set the inverter to charge when there's excess, and discharge otherwise. it will also respect charging slots.
# client.set_mode_dynamic()

# Check data is written
p = Plant(number_batteries=1)
client.refresh_plant(p, full_refresh=True)
print(p.inverter.charge_target_soc)
