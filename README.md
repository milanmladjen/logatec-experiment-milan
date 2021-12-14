# logatec-experiment

LOG-a-TEC testbed experiment repository template.\
Includes ready-made applications, Continuous Deployment service and Experiment Control & Monitoring System.

## Branches

Each supported technology has its own branch to work on.

* **SRDA** - 868 MHz ISM band
* **SRDB** - 2.4 GHz ISM band
* **LPWA** - LoRa 
* **BLE** - Bluetooth LE
* **UWB** - Ultra-Wide Band

## Deploy an experiment

1. Create an account on [Sensor Management System](https://videk.ijs.si) (SMS) portal and make a reservation request for a desired testbed resource. Experiment deployments without the reservation will be automatically declined.

2. Create a [fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) of the [template repository](https:/github.com/logatec3/logatec-experiment) and configure it to work with the Continuous Deployment service by:
   * adding a [Webhook](https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks) to your copy of the repository with secret access token provided at registration to SMS platform (Settings > Webhooks > Add a webhook) ,
   * adding the [logatec3](https://github.com/logatec3) user as a collaborator to your copy of the experiment repository (Settings > Manage access > Add people) .

3. Configure the `experiment-setup.conf` file where you can select the participating nodes, the experiment application and the experiment duration. `option=monitor` will include ECMS.

4. Draft a new release to trigger the autonomous experiment deployment and wait for a defined period of time.

5. Download the experiment results appended to the Release Assets.

## Testbed info

More info about the testbed can be found on the [official web-site](http://log-a-tec.eu/index.html "Official web-site").
