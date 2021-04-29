FROM sensorlab6/vesna-tools

# Set debian frontend
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Ljubljana

# Get dependencies
RUN set -ex \
	&& apt-get update --fix-missing \
	&& apt-get install -y \
					python3-pip \
					nano \
	&& apt-get clean

# Install pip3 packages
RUN set -ex \
	&& pip3 install pyserial \
					pyzmq

RUN mkdir logatec-experiment

WORKDIR /root/logatec-experiment

# contiki-ng is in .dockerignore, because it is too large to send it to Docker daemon
# and for copying it into container each time an docker image is build. That's why we
# Clone it from Github once and then it is cached...pull new changes inside container
RUN git clone --single-branch --branch master https://github.com/gcerar/contiki-ng.git

# Prepare folder for results
RUN mkdir results/

# Copy the logatec-experiment directory into container (without files in .dockerignore)
COPY ./ ./

# Start the deployment
ENTRYPOINT ["deployment/docker/start.sh"]
