# Description

All applications and experiments are located in the folders.

## Local test

Demo application uses bluepy python library. To install it locally on the LGTC machine, run:
> sudo apt-get install libglib2.0-dev python3-pip && sudo pip3 install bluepy

### Optional debug

In case that BT advertisement doesn't work in file */lib/systemd/system/bluetooth.service*
add *--experimental* flag to line 9 (or there around). It should look like this:
> ExecStart=/usr/lib/bluetooth/bluetoothd --experimental

## Testbed

To use autonomous testbed deployment, please follow already made templates or stick to the following rules:

* Application folder should have number indicator in front of the app name (XX_)
* The application script must have the same name as the folder name
* Start and stop advertisement (if needed) in */deployment/tasks/run-experiment* script.
