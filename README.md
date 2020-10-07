# logatec-experiment

Continuous delivery template - repository for making experiments in LOG-aTEC testbed with Contiki-NG OS.

## Get repository

To get the repository:
>```$ git clone git@github.com:logatec3/logatec-experiment.git```

To also get the sub-modules files:
>```$ git submodule update --init```

Do it in one step (but you will also get all nested sub-modules, which we usually do not need)
>```$ git clone --recurse-submodules git@github.com:logatec3/logatec-experiment.git```

**NOTE** \
`git pull` will only pull the changes of the base repo.
If you want to pull the changes of the sub-module as well use: ```$ git submodule update --remote``` \
You can also add `--merge` or `--rebase` to merge/rebase your branch with remote.

If you want to make some changes to the sub-modules, first checkout to the branch you want, then commit changes and push them.

## BLE branch

Branch for experiments with LGTCs Bluetooth module ([WL18MODGI](https://www.ti.com/product/WL1835MOD "Datasheet")).

To start advertising use ```$ sudo hciconfig hci0 leadv3``` and to stop advertising use ```$ sudo hciconfig hci0 noleadv```. \
If you want to get the MAC address of the device run ```sudo hciconfig | grep "BD Address"```. \
Some extra packages have to be installed for Bluetooth to work (see *Dockerfile*).

**NOTE** \
Contiki-NG and vesna-drivers are not needed for BT experiments (see *.dockerignore*). That's why:

* Sub-modules are not pulled from Github
* There is a separate image for docker containers called *lgtc-ble-experiment*

## Experiments

Follow the instructions in *readme.md* in folder applications.
