# logatec-experiment

LOG-a-TEC testbed experiment repository template.\
Includes ready-made applications, Continuous Deployment service and Experiment Control & Monitoring System.

## Sensor Radio Device A (868 MHz)

A branch for experiments with **SRD A** nodes.

Target node [VESNA](http://log-a-tec.eu/ap-cradio.html#hardware "Official web-site") is equipped with Atmel AT86RF212 and Texas Instruments CC2500 radio.

This branch currently supports only Atmels 868 GHz radio. Its drivers are located in the fork of [Contiki-NG OS](https://github.com/gcerar/contiki-ng) in folder `contiki-ng/arch/platform/vesna/dev/`. 

**NOTE**

Make sure that your submodules are on the right branch:

| submodule | branch |
| :-------: | :----: |
| contiki-ng | feature/rf212 |
| vesna-drivers | logatec-testbed |  
