# Description

Experiment application are located in the corresponding folders.

## Testbed

To use CD service, please refer to `../deployment/README.md`. 
Note that:

* experiment application folder should have number indicator (XX_),
* the application script must have the same name as the folder name.

## BLE module

Obtain the MAC address of the Bluetooth radio device:

`$ sudo hciconfig | grep "BD Address:`

Start BT advertisement:

`$ sudo hciconfig hci0 leadv3`

Stop BT advertisement:

`$ sudo hciconfig hci0 noleadv`


In case that BT advertisement doesn't work, add a *--experimental* flag in file `/lib/systemd/system/bluetooth.service` line 9.
Something like:

> ExecStart=/usr/lib/bluetooth/bluetoothd --experimental