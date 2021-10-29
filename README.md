# logatec-experiment

Continuous delivery template - deployment of experiments in the LOG-a-TEC testbed.

## SRDB branch

Branch for experiments with **SRD B** devices - Vesna equipped with Atmel AT86RF231 and Texas Instruments CC1101 radios. 
[More info](http://log-a-tec.eu/ap-cradio.html#hardware "Official web-site").

This branch is focused on experiments with Atmels 2.4 GHz radio. Drivers for it are located in our fork of [Contiki-NG OS](https://github.com/gcerar/contiki-ng) in folder *contiki-ng/arch/platform/vesna/dev/*. 

**NOTE**

Make sure that your submodules are on the right branch:

| submodule | branch |
| :-------: | :----: |
| contiki-ng | master |
| vesna-drivers | logatec-testbed | 

<br>

## Experiments

To make an experiment follow the instructions in *README.md* in folder applications.
