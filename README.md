# logatec-experiment

LOG-a-TEC testbed experiment repository with included Continuous Deployment service and Experiment Control & Monitoring System.

## Sensor Radio Device B (2.4 GHz)

A branch for experiments with **SRD B** nodes.

Target node [VESNA](http://log-a-tec.eu/ap-cradio.html#hardware "Official web-site") is equipped with Atmel AT86RF231 and Texas Instruments CC1101 radio.

This branch is currently supporting only Atmels 2.4 GHz radio. Its drivers are located in the fork of [Contiki-NG OS](https://github.com/gcerar/contiki-ng) in folder `contiki-ng/arch/platform/vesna/dev/`. 

**NOTE**

Make sure that your submodules are on the right branch:

| submodule | branch |
| :-------: | :----: |
| contiki-ng | master |
| vesna-drivers | logatec-testbed | 
