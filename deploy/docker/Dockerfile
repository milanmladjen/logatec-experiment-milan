FROM sensorlab6/vesna-tools

# Set debian frontend
ENV DEBIAN_FRONTEND=noninteractive

# Get dependencies
RUN apt-get update --fix-missing && \
	apt-get install -y python-pip python3-pip python-numpy nano && \
	apt-get clean && \
	pip3 install pyserial

RUN mkdir LOG-a-TEC-testbed

WORKDIR /root/LOG-a-TEC-testbed

# contiki-ng is in .dockerignore, because it is too large to send it to Docker daemon
# and for copying it into container each time an docker image is build. That's why we
# Clone it from Github once and then it is cached...pull new changes inside container
RUN git clone --single-branch --branch master https://github.com/gcerar/contiki-ng.git

# Copy the LOG-a-TEC-testbed directory into container (without files in .dockerignore)
COPY ./ ./

# Start the deployment
ENTRYPOINT ["deploy/docker/start.sh"]
