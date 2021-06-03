PROJECT_SOURCES = benchmark.c
CONTIKI_PROJECT = benchmark

all: $(CONTIKI_PROJECT)

CONTIKI := ../../contiki-ng
VSNDRIVERS := ../../vesna-drivers

TARGET = vesna
AT86RF2XX_BOARD = ISMTV_v1.1


MAKE_MAC = MAKE_MAC_TSCH

#MODULES += os/services/shell


include $(CONTIKI)/Makefile.include
