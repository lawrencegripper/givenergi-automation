#!/usr/bin/env python3

import os
import sys
from time import timezone
import backoff
from pysolcast.rooftop import RooftopSite
from givenergy_modbus.client import GivEnergyClient
from givenergy_modbus.model.inverter import Model
from givenergy_modbus.model.plant import Plant
import requests
import tinytuya

def send_signal(msg):
    signal_request = {
        "number": os.environ["SIGNAL_SEND"],
        "recipients": [ os.environ["SIGNAL_RECEIVE"] ],
        "message": msg,
    }
    print(f"Sending signal message: {signal_request}")
    requests.post("http://ubuntu-utilities:30027", json = signal_request)

def on_backoff(details):
    print(f"Backing off {details['wait']} seconds afters {details['tries']} tries calling function {details['target']}. Args: {details['args']}, kwargs: {details['kwargs']}")
    type, value, traceback = sys.exc_info()
    print(value)
    print(traceback)

@backoff.on_exception(backoff.expo, Exception, max_tries=5, on_backoff=on_backoff)
def get_surplus_from_inverter():
    client = GivEnergyClient(host=os.environ["INVERTOR_IP_1"])
    p = Plant(number_batteries=1)
    client.refresh_plant(p, full_refresh=True)
    return (p.inverter.p_pv1 + p.inverter.p_pv2) - p.inverter.p_load_demand

# Connect to Device
d = tinytuya.OutletDevice(
    dev_id=os.getenv('IMERSION_SWITCH_DEVICE_ID'),
    address=os.getenv('IMERSION_SWITCH_IP'),
    local_key=os.getenv('IMERSION_SWITCH_LOCAL_KEY'),
    version=os.getenv('IMERSION_SWITCH_TUYA_VERSION'))

# Get Status
data = d.status()
print('set_status() result %r' % data)
print(d.detect_available_dps())

# Plugs and switches descriptions
current_kwh_usage = data['dps']['17']
current_surplus = get_surplus_from_inverter()
currently_on = data['dps']['1']

# print(f"Current usage: {current_kwh_usage}")
print(f"Current surplus: {current_surplus}")
print(f"Currently on?: {currently_on}")

if currently_on and (current_surplus < 0):
    d.turn_off()
    send_signal(f"Turned off imersion heater. Surplus: {current_surplus}")
    exit(0)

if not currently_on and (current_surplus > 3000):
    d.turn_on()
    send_signal(f"Turned on imersion heater. Surplus: {current_surplus}")
    exit(0)

send_signal(f"Imersion heater not changed. Surplus: {current_surplus}. Currently on?: {currently_on}")