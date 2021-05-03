# Description of deployment process

TODO

## Ansible playbook

TODO

## Docker

Infrastructure nodes (LGTC) in the testbed are using Docker containers for compiling and programing guest target nodes (VESNA).
Container image in this directory is build on top of [vesna-tools-v2 image](https://github.com/sensorlab/sna-lgtc-support/tree/master/docker), version 2.
Each experiment has its own version of Dockerfile, stored in folder docker.

### Notes

* Use `-f deployment/docker/Dockerfile` flag while building Docker image, to COPY whole logatec-experiment folder.
* Contiki-NG folder is too large to be sent into Docker daemon. That's why it is included in .dockerignore file and cloned while container is building. Because of caching, pull the latest changes inside of container.

## Tasks

TODO