# logatec-experiment

Continuous delivery template - deployment of experiments in the LOG-a-TEC testbed.

## SRD A branch

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