import pycom
import machine
from machine import Pin

pycom.heartbeat(False)

from network import WLAN
from network import Bluetooth
import os

pycom.wifi_on_boot(False)
wlan = WLAN()                               # Instantiates WLAN
wlan.deinit()                               # Turns off wifi
bluetooth = Bluetooth()                     # Instantiates Bluetooth
bluetooth.deinit()                          # Turns off Bluetooth

counter=pycom.nvs_get('count')              # Get ID value from memory

if type(counter)!= int:                     # If the value is not in memory
    pycom.nvs_set('count', 0)               # ID = 0
