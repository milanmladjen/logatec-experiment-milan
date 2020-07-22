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
RUN git clone --single-branch --branch stats-app https://github.com/gcerar/contiki-ng.git
#WORKDIR /root/vesna-management-system
#RUN ant build

#RUN git clone --single-branch --branch grega https://github.com/gcerar/contiki-ng.git
#WORKDIR /root/contiki-ng/
#ARG time 
#RUN git pull

# Copy source
COPY . /root/contiki-ng/arch/platform/vesna/vesna-drivers
WORKDIR /root/contiki-ng/arch/platform/vesna/vesna-drivers

ENTRYPOINT ["docker/start.sh"]

