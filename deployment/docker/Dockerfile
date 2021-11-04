# From base image
FROM sensorlab6/vesna-tools-v2:latest

# Install dependencies for experiment
RUN set -ex \
    && apt-get update --fix-missing \
    && apt-get install -y 	nano \
                       		python3-pip \
							python3-numpy \					   
							git \		
	&& apt-get clean -y

# Install Python3 libs
RUN set -ex \
	&& pip3 install 	pyzmq \
						pyserial \
						Adafruit_BBIO

# Install stm32flash (flashing UWB)
RUN set -ex \
	&& git clone https://github.com/stm32duino/stm32flash.git \
	&& cd /root/stm32flash/ \
	&& make \
	&& make install 

# Prepare folder for experiment files
RUN mkdir logatec-experiment

WORKDIR /root/logatec-experiment

# Prepare folder for results
RUN mkdir results/

# Copy the logatec-experiment directory into container (without files in .dockerignore)
COPY ./ ./

# Start the deployment
ENTRYPOINT ["deployment/docker/start.sh"]