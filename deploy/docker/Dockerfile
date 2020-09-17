FROM sensorlab6/vesna-tools

# Set debian frontend
ENV DEBIAN_FRONTEND=noninteractive

# Dependencies
RUN apt-get update --fix-missing && \
	apt-get install -y python-pip python3-pip python-numpy python-lxml nano && \
	apt-get clean && \
	pip3 install pyserial

#TODO why do we need lxml?

WORKDIR /root/

RUN mkdir LOG-a-TEC-testbed

# Copy the LOG-a-TEC-testbed directory into container
COPY ../../../LOG-a-TEC-testbed /root/LOG-a-TEC-testbed/

WORKDIR /root/LOG-a-TEC-testbed

ENTRYPOINT ["deploy/docker/start.sh"]

