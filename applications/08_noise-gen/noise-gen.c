/* ----------------------------------------------------------------------------
 * NOISE GENERATION - AT86RF212 CONTINUOUS TRANSMISSION TEST MODE 
 * 
 * You must enter the application duration here (and in serial_monitor.py)
 * ----------------------------------------------------------------------------
*/
#include <stdio.h>
#include "contiki.h"
#include "../../contiki-ng/arch/platform/vesna/dev/at86rf2xx/rf2xx.h"
#include "../../vesna-drivers/VESNALib/inc/vsntime.h" // For delayS

/*---------------------------------------------------------------------------*/
// Set durration of the app in seconds
#define APP_DURATION_IN_SEC     (60 * 60)

// Set freq from 857 - 882.5 MHz (857 + 0.1*CC_NUMBER) (datasheet p. 123)
#define CC_NUM                  (110) //868MHz

// Set power of transmission, from -11dBm ti 2dBm...see rf2xx_registermap.h
#define POWER                   (TX_POWER_n11)

/*---------------------------------------------------------------------------*/
PROCESS(continuous_transmission_test_mode_process, "CTTM process");
AUTOSTART_PROCESSES(&continuous_transmission_test_mode_process);

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(continuous_transmission_test_mode_process, ev, data){

    static struct etimer timer;

    PROCESS_BEGIN();

    printf("Set radio to: continuos transmission test mode. \n");
    rf2xx_CTTM_start(POWER, CC_NUM);

    vsnTime_delayS(APP_DURATION_IN_SEC);

    rf2xx_CTTM_stop();
    printf("Stop continuos transmission test mode. \n");

    while(1){}

    PROCESS_END();
}