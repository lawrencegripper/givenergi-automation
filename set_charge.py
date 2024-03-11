#!/usr/bin/env python3



# Solcast give limited free API calls, so cache the data for testing
import datetime
import os
import sys
from time import timezone
import backoff
from pysolcast.rooftop import RooftopSite
import json
from givenergy_modbus.client import GivEnergyClient
from givenergy_modbus.model.inverter import Model
from givenergy_modbus.model.plant import Plant
import requests
import subprocess

currentDateAndTime = datetime.datetime.now()
print("The current date and time is", currentDateAndTime)
print(subprocess.check_output("date", shell=True).decode())

def send_signal(msg):
    signal_request = {
        "number": os.environ["SIGNAL_SEND"],
        "recipients": [ os.environ["SIGNAL_RECEIVE"] ],
        "message": msg,
    }
    requests.post("http://restapi.signal.svc.cluster.local", json = signal_request)


def on_backoff(details):
    print(f"Backing off {details['wait']} seconds afters {details['tries']} tries calling function {details['target']}. Args: {details['args']}, kwargs: {details['kwargs']}")
    type, value, traceback = sys.exc_info()
    print(value)
    print(traceback)
    send_signal(f"Backing off {details['wait']} seconds afters {details['tries']} tries calling function. Error: {value}")

@backoff.on_exception(backoff.expo, Exception, max_tries=5, on_backoff=on_backoff)
def update_inverter(predicted_charge_percentage):
    # Connect to inverter
    client = GivEnergyClient(host=os.environ["INVERTOR_IP_1"])

    # Set data
    client.set_battery_target_soc(predicted_charge_percentage)
    # Warning this timing is in UTC not BST/Local time
    client.set_charge_slot_1((datetime.time(hour=1, minute=00), datetime.time(hour=4, minute=00)))
    # # set the inverter to charge when there's excess, and discharge otherwise. it will also respect charging slots.
    # client.set_mode_dynamic()

    # Check data is written
    p = Plant(number_batteries=1)
    client.refresh_plant(p, full_refresh=True)
    send_signal(f"Confirmed overnight charge set to {p.inverter.charge_target_soc}%")

    print(p.inverter.charge_target_soc)

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
    forecasts = site.get_forecasts().get('forecasts')
    json_str = json.dumps(forecasts, indent=4)
    with open('forcast-cache.json', 'w') as cache_file:
        json.dump(forecasts, cache_file, indent=4)

# Caculate predicted generation tomorrow from the forcast
tomorrow = datetime.date.today() + datetime.timedelta(days=1)
day_after_tomorrow = datetime.date.today() + datetime.timedelta(days=2)

# parse iso8601 date strings into datetime objects
for f in forecasts:
    f["parsed"] = datetime.datetime.fromisoformat(f["period_end"])

# filter forcast to just tomorrow
tomorrow_forecasts = list(filter(lambda c: c.get("parsed").date() >= tomorrow and c.get("parsed").date() < day_after_tomorrow, forecasts))

# Sum the generation for tomorrow
predicted_generation = sum([f.get("pv_estimate")/2 for f in tomorrow_forecasts])
print(f"Predicted generation for tomorrow: {predicted_generation}")

# This is how much we need to get to sunrise
BATTERY_MIN_CHARGE = 22

# Update overnight change percentage based on forecast
# ... Let's do some bad maths....
battery_capacity_kw = 9.5
house_direct_solar_consumption_kw = 15
total_usage_kw = (house_direct_solar_consumption_kw + battery_capacity_kw)
print(f"Total estimated usage: {total_usage_kw}")

if total_usage_kw > predicted_generation:
    predicted_charge_percentage = ((total_usage_kw - predicted_generation) / battery_capacity_kw) * 100
else:
    print("We have enough generation to cover usage. Using min change value")
    predicted_charge_percentage = BATTERY_MIN_CHARGE

print(f"Predicted charge percentage: {predicted_charge_percentage}")

if predicted_charge_percentage > 100:
    predicted_charge_percentage = 100

msg = f"Set overnight charge percentage to {predicted_charge_percentage}%\n\nPredicted generation for tomorrow: {predicted_generation}kwh\nTotal estimated usage: {total_usage_kw}kwh"
send_signal(msg)

update_inverter(int(predicted_charge_percentage))
