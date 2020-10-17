# logatec-experiment

Continuous delivery template - repository for making experiments in LOG-aTEC testbed with Contiki-NG OS.

More info about the testbed can be found [here](http://log-a-tec.eu/ap-cradio.html#jsi-campus "Official web-site").

## Get the repository

To get the repository:
>```$ git clone git@github.com:logatec3/logatec-experiment.git```

To also get the sub-modules files:
>```$ git submodule update --init```

Do it in one step (but you will also get all nested sub-modules, which we usually do not need)
>```$ git clone --recurse-submodules https://github.com/logatec3/logatec-experiment.git```

**NOTE** \
`git pull` will only pull the changes of the base repo.
If you want to pull the changes of the sub-module as well use: ```$ git submodule update --remote```.
You can also add `--merge` or `--rebase` to merge/rebase your branch with remote.

If you want to make some changes to the sub-modules, first checkout to the branch you want, then commit changes and push them.

## SRDA branch

Branch for experiments with **SRD A** devices - Vesna equipped with Atmel AT86RF212 and Texas Instruments CC2500 radios. 
[More info](http://log-a-tec.eu/ap-cradio.html#hardware "Official web-site").

This branch is focused on experiments with Atmels 868 MHz radio. Drivers for it are located in our fork of [Contiki-NG OS](https://github.com/gcerar/contiki-ng) in folder *contiki-ng/arch/platform/vesna/dev/*. 

**NOTE**

Make sure that your submodules are on the right branch:

| submodule | branch |
| :-------: | :----: |
| contiki-ng | feature/rf212 |
| vesna-drivers | logatec-testbed | 

<br>

## Experiments

To make an experiment follow the instructions in *README.md* in folder applications.