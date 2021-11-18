# CD Service

Continuous Deployment service, built with Docker containers and orchestrated with Ansible engine, deploys the experiment application to the selected nodes in the testbed. 

![Continuous Deployment reference architecture.](deployment.png)
## Ansible playbook

CD service starts with the main `../Makefile` which executes 3 Ansible playbooks (located in folder `ansible/`):
* `release_controller.yml` - optional - deploys the *ECMS_monitor* to the *Management Server* - more info in the folder `../monitor/`,
* `release_targets.yml` - deploys the experiment application to selected devices, 
* `collect_results.yml` - collects results and forwards them back to the user.

Before deploying, select desired variables in the Ansible playbook `release_targets.yml`:
> * **hosts** - use an IP address, technology name, or cluster name in your inventory file.
> * **application** - select application folder.
> * **duration** - define the maximal experiment duration. 
> * **option** - add option for [*task*](#Tasks) execution. Default is *none*.

### **Notes**

* *hosts* for the `collect_results.yml` MUST be the same as in `release_targets.yml`!
* strategy: free - enables parallel execution. All the nodes will run simultaneously but they will not wait for each other.
* `-f 50` is allowing Ansible to make 50 forks at the same time.
* `-i ` flag determines the inventory file - default is `ansible/inventory/logatec_testbed.ini`. You can add new clusters in your inventory file.

## Docker

Experiment application is executed inside a Docker container. Container images are build on top of [vesna-tools-v2 image](https://github.com/sensorlab/sna-lgtc-support/tree/master/docker), version 2.
Each technology branch has its own version of Dockerfile (stored in folder `docker/`) including all the necessary drivers and libraries.

At startup, Docker container will execute `docker/start.sh` script. The script checks for given parameters = options and executes the corresponding task with `tasks/Makefile`.
### **Notes**

* `-f deployment/docker/Dockerfile` flag is used while building Docker image, to COPY the whole logatec-experiment folder.
* Contiki-NG folder is too large to be sent into Docker daemon. Therefore it is included in `../.dockerignore` and cloned from GH while container is building. Since Docker uses cache, pull the latest changes from the container.

## Tasks

*Task script* `tasks/run-experiment-...` will prepare the device (compile the application, flash the target device, ...) and execute the experiment application. Each *task script* is prepared for different scenario (master node, coordinator, simple node, option to monitor experiment execution, etc.). `tasks/Makefile` will execute appropriate *script* by given option parameter in the Ansible playbook.

### **Notes**

* Devices in the testbed are distinguished by their last 3 digits of IP address - experiment results filename should include this number.
* At the end of experiment the results must be moved to the folder `logatec-experiment/results/` (which is created inside the Docker container).