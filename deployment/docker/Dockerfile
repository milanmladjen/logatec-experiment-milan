# -------------------------------------------------------------------------------------
# Vesna-drivers dockerfile - ubuntu instead of debian (problems with python3.6)
# -------------------------------------------------------------------------------------
FROM arm32v7/ubuntu:focal

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Ljubljana

# Install dependences
RUN set -ex \
	&& apt-get update --fix-missing \
	&& apt-get upgrade -y \
	&& apt-get install -y   apt-utils \
	&& apt-get clean -y
					
# Install dependences for vena drivers
RUN set -ex \
	&& apt-get install -y   gcc-arm-none-eabi \
							#GDB not found in ubuntu dep... do we even need it?
							#gdb-arm-none-eabi \ 
							libnewlib-arm-none-eabi \
							devscripts \
							git \
	&& apt-get clean -y

# Install dependences for vesna management system
RUN	set -ex \
	&& apt-get install -y	default-jdk \
							ant \
							librxtx-java \
	&& apt-get clean -y

RUN apt-get install -y equivs

# Install OpenOCD
# "touch" commands to avoid occasional "aclocal-1.13: command not found" errors.
# https://stackoverflow.com/a/30386141
RUN	git clone -b sna-lgtc https://github.com/avian2/openocd.git && \
	cd openocd && \
	touch configure.ac aclocal.m4 configure && \
	find . -name Makefile.in -exec 'touch' '{}' ';' && \
	mk-build-deps --install -t "apt-get -y --no-install-recommends" && \
	dpkg-buildpackage -uc -b && \
	cd .. && \
	dpkg -i openocd_*.deb && \
	apt-get clean && \
	apt-get remove -y openocd-build-deps && \
	apt-get autoremove -y && \
	rm -rf openocd && \
	rm -f openocd_*.deb openocd_*.changes



# -------------------------------------------------------------------------------------
# Experiment Dockerfile
# -------------------------------------------------------------------------------------

# Install dependencies for experiment
RUN set -ex \
    && apt-get update --fix-missing \
	#&& apt-get upgrade -y \
    && apt-get install -y 	nano \
                       		python3-pip \
	&& apt-get clean -y

RUN set -ex \
	&& pip3 install pyzmq \
					pyserial

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