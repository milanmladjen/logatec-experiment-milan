FROM sensorlab6/vesna-tools

# Set debian frontend
ENV DEBIAN_FRONTEND=noninteractive

# Get dependencies
RUN apt-get update --fix-missing && \
	apt-get install -y python-pip python3-pip nano \
	bluetooth bluez bluez-tools libglib2.0-dev && \
	apt-get clean && \
	pip3 install pyserial bluepy

RUN mkdir logatec-experiment

WORKDIR /root/logatec-experiment

# Prepare folder for results
RUN mkdir results/

# Copy the logatec-experiment directory into container (without files in .dockerignore)
COPY ./ ./

# Start the deployment
ENTRYPOINT ["deployment/docker/start.sh"]

# TODO: Uredi ta Dockerfile tako, da bo kompatibilen sz vesna-tools-v2...naprave bodo u bodoče imele samo en image, drugače bo preveč prostora šlo..
# Ceuga uredi, tudi apt-get del..