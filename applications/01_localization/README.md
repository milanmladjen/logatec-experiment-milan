# Description

Devices in the testbed scan for BLE beacons. If phone is found, its received signal strength indicator (RSSI) is sent to the Management Server.

# Note

Change PHONE_NAME.


# Obtaining fingerprints
To distinguish between different positions, use ECMS to send new location start and end positions (L1S, L1E and so on). Use parsers to obtain the data and use it in the frontend JS script.