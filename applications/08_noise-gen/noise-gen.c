/* ----------------------------------------------------------------------------
 * NOISE GENERATION - AT86RF212 CONTINUOUS TRANSMISSION TEST MODE 
 * 
 * Use radios CTTM to generate noise on certain freqency. 
 * TODO: not tested yet in the testbed
 * ----------------------------------------------------------------------------
*/
#include <stdio.h>
#include "contiki.h"
#include "../../contiki-ng/arch/platform/vesna/dev/at86rf2xx/rf2xx.h"
#include "../../vesna-drivers/VESNALib/inc/vsntime.h" // For delayS

/*---------------------------------------------------------------------------*/
// Set durration of the app in seconds
#define DEFAULT_APP_DUR_IN_SEC     (60 * 60)

// Set freq from 857 - 882.5 MHz (857 + 0.1*CC_NUMBER) (datasheet p. 123)
#define CC_NUM                  (110) //868MHz

// Set power of transmission, from -11dBm ti 2dBm...see rf2xx_registermap.h
#define POWER                   (TX_POWER_n11)

// If there is no communication from LGTC, go with default
uint32_t app_duration = DEFAULT_APP_DUR_IN_SEC;

/*---------------------------------------------------------------------------*/
PROCESS(continuous_transmission_test_mode_process, "CTTM process");
PROCESS(serial_input_process, "Serial input command");
AUTOSTART_PROCESSES(&serial_input_process);

/*---------------------------------------------------------------------------*/
void input_command(char *data);

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(serial_input_process, ev, data)
{
    PROCESS_BEGIN();
    while(1){
		PROCESS_WAIT_EVENT_UNTIL((ev == serial_line_event_message) && (data != NULL));
		input_command(data);
    }
    PROCESS_END();
}

/*---------------------------------------------------------------------------*/
void
input_command(char *data){
	
    char cmd = data[0];
	char time[8];
    char cc[3];
	char *p;
    switch(cmd){
		case '>':
			process_start(&continuous_transmission_test_mode_process, NULL);
			break;

		//case '*':
		//	set_device_as_root();
		//	break;

		case '=':
			printf("= \n");	// Confirm received stop command
			process_exit(&continuous_transmission_test_mode_process);
			break;

		case '&':
			p = data + 1;
			strcpy(time, p);
			app_duration = atoi(time);
			printf("App duration %ld \n", app_duration);
			break;

		default:
			printf("Unknown cmd \n");
			break;
    }
}

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(continuous_transmission_test_mode_process, ev, data){

    static struct etimer timer;

    PROCESS_BEGIN();

    // Send start command ('>') back to LGTC so it knows we started process
	printf("> \n");

    printf("Set radio to: continuos transmission test mode. \n");
    rf2xx_CTTM_start(POWER, CC_NUM);

    vsnTime_delayS(app_duration);

    rf2xx_CTTM_stop();
    printf("Stop continuos transmission test mode. \n");

    // Send stop command ('=') to LGTC
    printf("= \n");	

    while(1){}

    PROCESS_END();
}