CONTIKI_PROJECT = stats-app
all: $(CONTIKI_PROJECT)

AT86RF2XX_BOARD = ISMTV_v1.1

TARGET=vesna

PROJECT_SOURCES = experiment.c

#VESNA= ../../arch/platform/vesna/vesna-drivers/

CONTIKI := ../contiki-ng
VSNDRIVERS := ../vesna-drivers

#CFLAGS += -DPROJECT_CONF_PATH=\"./project-conf.h\"

MAKE_MAC = MAKE_MAC_TSCH

include $(CONTIKI)/Makefile.include
