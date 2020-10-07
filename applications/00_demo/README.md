# Demo application

Example how to use BT on LGTC

## get bt mac address

sudo hciconfig | grep "BD Address:"

## use this command to start BT advertisment

sudo hciconfig hci0 leadv3

## use this command to stop BT advertisment

sudo hciconfig hci0 noleadv
