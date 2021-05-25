PROJECT_SOURCES = acs.c
CONTIKI_PROJECT = acs
all: $(CONTIKI_PROJECT)

CONTIKI := ../../contiki-ng
VSNDRIVERS := ../../vesna-drivers

TARGET = vesna
AT86RF2XX_BOARD = ISMTV_v1.1

PLATFORMS_EXCLUDE = sky z1 nrf52dk native
BOARDS_EXCLUDE = srf06/cc13x0 launchpad/cc1310 launchpad/cc1350 sensortag/cc2650 sensortag/cc1350

include $(CONTIKI)/Makefile.dir-variables

# The channel selection library
MODULES += $(CONTIKI_NG_SERVICES_DIR)/tsch-cs

# force Orchestra from command line
MAKE_WITH_ORCHESTRA ?= 0
# force Security from command line
MAKE_WITH_SECURITY ?= 0
# print #routes periodically, used for regression tests
MAKE_WITH_PERIODIC_ROUTES_PRINT ?= 1

MAKE_MAC = MAKE_MAC_TSCH

#MODULES += $(CONTIKI_NG_SERVICES_DIR)/shell

ifeq ($(MAKE_WITH_ORCHESTRA),1)
MODULES += $(CONTIKI_NG_SERVICES_DIR)/orchestra
endif

ifeq ($(MAKE_WITH_SECURITY),1)
CFLAGS += -DWITH_SECURITY=1
endif

ifeq ($(MAKE_WITH_PERIODIC_ROUTES_PRINT),1)
CFLAGS += -DWITH_PERIODIC_ROUTES_PRINT=1
endif

include $(CONTIKI)/Makefile.include
