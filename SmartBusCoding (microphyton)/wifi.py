#HEMA SAUNDARASAN
#52224123036

#connect_wifi.py
import network
import time

ssid = "RMHPS-2.4"
password = "0530252218"

wlan = network.WLAN(network.STA_IF)

# Reset WiFi properly
wlan.active(False)
time.sleep(1)
wlan.active(True)

print("Connecting to WiFi...")

wlan.connect(ssid, password)

# Wait until connected
timeout = 15  # seconds
start = time.time()

while not wlan.isconnected():
    if time.time() - start > timeout:
        print("Connection FAILED ❌")
        break
    print("Still connecting...")
    time.sleep(1)

if wlan.isconnected():
    print("Connected ✅")
    print("IP:", wlan.ifconfig())
