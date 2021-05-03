# From base image
FROM sensorlab6/logatec-experiment:latest

# Install dependencies for experiment
RUN set -ex \
    && apt-get update --fix-missing \
    && apt-get install -y 	nano \
                       		python3-pip \
	&& apt-get clean -y

# Install Python3 libs
RUN set -ex \
	&& pip3 install 	pyzmq \
						pyserial

# Prepare folder for experiment files
RUN mkdir logatec-experiment

WORKDIR /root/logatec-experiment

# Prepare folder for results
RUN mkdir results/

# Pull the changes inside a container!
RUN git clone --single-branch --branch master https://github.com/gcerar/contiki-ng.git

# Copy the logatec-experiment directory into container (without files in .dockerignore)
COPY ./ ./

# Start the deployment
ENTRYPOINT ["deployment/docker/start.sh"]