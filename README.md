# logatec-experiment

Continuous delivery template - deployment of experiments in the LOG-a-TEC testbed.

## Branches

Each supported technology has its own branch to work on.

* **SRDA** - 868 MHz ISM band
* **SRDB** - 2.4 GHz ISM band
* **LPWA** - LoRa 
* **BLE** - Bluetooth LE
* **UWB** - Ultra Wide Band

## Testbed info

More info about the testbed can be found on the [official web-site](http://log-a-tec.eu/index.html "Official web-site").

## Get repository

To get the repository:
$ git clone git@github.com:logatec3/logatec-experiment.git

Some technologies use submodules. You can get them with:
$ git submodule update --init

Do it in one step:
$ git clone --recurse-submodules git@github.com:logatec3/logatec-experiment.git

**NOTE** \
`git pull` will only pull the changes of the base repo.
If you want to pull the changes of the sub-module as well use: ```$ git submodule update --remote``` \
You can also add `--merge` or `--rebase` to merge/rebase your branch with remote.

If you want to make some changes to the sub-modules, first checkout to the branch you want, then commit changes and push them.
