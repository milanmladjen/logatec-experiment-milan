FROM sensorlab6/vesna-tools-v2:latest

# Install dependencies for the experiment
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

# Copy the logatec-experiment directory into container (without files in .dockerignore)
COPY ./ ./

# Start the experiment
ENTRYPOINT ["deployment/docker/start.sh"]