PROJECT_SOURCES = multicast.c multicast-root.c
CONTIKI_PROJECT = multicast multicast-root

all: $(CONTIKI_PROJECT)

CONTIKI := ../../contiki-ng
VSNDRIVERS := ../../vesna-drivers

TARGET=vesna
AT86RF2XX_BOARD = ISMTV_v1.1


MAKE_MAC = MAKE_MAC_TSCH
MAKE_ROUTING = MAKE_ROUTING_RPL_CLASSIC

include $(CONTIKI)/Makefile.identify-target
MODULES_REL += $(TARGET)

include $(CONTIKI)/Makefile.dir-variables
MODULES += $(CONTIKI_NG_NET_DIR)/ipv6/multicast

include $(CONTIKI)/Makefile.include
