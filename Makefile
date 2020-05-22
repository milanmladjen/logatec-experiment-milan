CONTIKI_PROJECT = stats-app
all: $(CONTIKI_PROJECT)

MAKE_MAC = MAKE_MAC_TSCH

AT86RF2XX_BOARD = ISMTV_v1.1
TARGET=vesna


PROJECT_SOURCES= stats-app.c
#PROJECT_SOURCES= vsndriversconf.c stats-app.c
#PROJECT_HEADERS= vsndriversconf.h

#VESNA= ../../arch/platform/vesna/vesna-drivers/

CONTIKI := ./contiki-ng
VSNDRIVERS := ./vesna-drivers

#CFLAGS += -DPROJECT_CONF_PATH=\"./project-conf.h\"

include $(CONTIKI)/Makefile.include
