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
RUN git clone --single-branch --branch master https://github.com/logatec3/LOG-a-TEC-testbed.git	
#TODO branch nej bo tisti na katerem delamo...torej za SRDA plate nej bo branch SRDA

# TODO 
# If "git submodule update --init" doesnt work without uname and passwd, copy vesna-drivers from here to the docker container
COPY ../../vesna-drivers /root/LOG-a-TEC-testbed/contiki-ng/arch/platform/vesna/vesna-drivers

WORKDIR /root/LOG-a-TEC-testbed

ENTRYPOINT ["deploy/docker/start.sh"]

