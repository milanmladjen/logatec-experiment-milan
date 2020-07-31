/* -----------------------------------------------------------------------------
 * APPLICATION FOR MEASURING STATISTICS OF THE NETWORK
 * -----------------------------------------------------------------------------
*/

#include "contiki.h"
#include <stdio.h>
#include <stdlib.h>
#include "dev/serial-line.h"
#include "../../contiki-ng/arch/platform/vesna/dev/at86rf2xx/rf2xx_stats.h"

/*---------------------------------------------------------------------------*/
#define SECOND						(1000)
#define DEFAULT_APP_DUR_IN_SEC		(60 * 60)
#define BGN_MEASURE_TIME_MS			(10)

uint32_t app_duration = DEFAULT_APP_DUR_IN_SEC;

enum STATS_commands {cmd_start, cmd_stop, cmd_appdur};
/*---------------------------------------------------------------------------*/
void STATS_print_help(void);
void STATS_input_command(char *data);
void STATS_output_command(uint8_t cmd);
void STATS_set_device_as_root(void);
void STATS_close_app(void);

/*---------------------------------------------------------------------------*/
PROCESS(stats_process, "Stats app process");
PROCESS(serial_input_process, "Serial input command");
PROCESS(bgn_process, "Background noise process");

AUTOSTART_PROCESSES(&serial_input_process);

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(serial_input_process, ev, data)
{
    PROCESS_BEGIN();
    while(1){
      PROCESS_WAIT_EVENT_UNTIL(
        (ev == serial_line_event_message) && (data != NULL));
      STATS_input_command(data);
    }
    PROCESS_END();
}

void
STATS_input_command(char *data){
    char cmd = data[0];
	char time[8];
	char *p;
    switch(cmd){
		case '>':
			process_start(&stats_process, NULL);
			process_start(&bgn_process, NULL);
			break;

		case '*':
			STATS_set_device_as_root();
			break;

		case '=':
			process_exit(&stats_process);
			process_exit(&bgn_process);
			STATS_close_app();
			break;

		case '&':
			p = data + 1;
			strcpy(time, p);
			app_duration = atoi(time);
			STATS_output_command(cmd_appdur);
			break;

		default:
			break;
    }
}

void
STATS_output_command(uint8_t cmd)
{
	switch(cmd){
		case cmd_start:
			printf("> \n");
			break;

		case cmd_stop:
			printf("= \n");
			break;

		case cmd_appdur:
			printf("App duration %ld\n", app_duration);
			break;
		
		default:
			printf("Unknown output command \n");
			break;
	}
}

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(bgn_process, ev, data)
{
	static struct etimer bgn_timer;

	PROCESS_BEGIN();

	etimer_set(&bgn_timer, BGN_MEASURE_TIME_MS);

	while(1){
		STATS_update_background_noise();

		PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&bgn_timer));
		etimer_reset(&bgn_timer);
	}
	PROCESS_END();
}

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(stats_process, ev, data)
{
	static struct etimer timer;
	static uint32_t time_counter = 0;

	PROCESS_BEGIN();

	// Respond to LGTC
	STATS_output_command(cmd_start);

	time_counter = 0;  

	// Empty buffers if they have some values from before
	RF2XX_STATS_RESET();
	STATS_clear_packet_stats();
	STATS_clear_background_noise();

	STATS_print_help();

	etimer_set(&timer, SECOND);

	while(1) {	

		if((time_counter % 10) == 0){
			STATS_print_packet_stats();
			STATS_print_background_noise();
		}
		
		// After max time send stop command ('=') and print driver statistics
		if(time_counter == (app_duration)){
			STATS_close_app();
			PROCESS_EXIT();
		}

		// Wait for the periodic timer to expire and then restart the timer.
		PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&timer));
		etimer_reset(&timer);

		// Second has passed
		time_counter++;
	}

	PROCESS_END();
}

/*---------------------------------------------------------------------------*/
void
STATS_set_device_as_root(void){
	if(!NETSTACK_ROUTING.node_is_root()) {
		NETSTACK_ROUTING.root_start();
	} else {
		printf("Node is already a DAG root\n");
	}
}

/*---------------------------------------------------------------------------*/
void
STATS_close_app(void){

	STATS_print_driver_stats();
	
	// Send '=' cmd to stop the monitor
	STATS_output_command(cmd_stop);

	// Empty buffers
	RF2XX_STATS_RESET();
	STATS_clear_packet_stats();
	STATS_clear_background_noise();

	// Reset the network
	if(NETSTACK_ROUTING.node_is_root()){
		NETSTACK_ROUTING.leave_network();
	}
}

/*---------------------------------------------------------------------------*/
void
STATS_print_help(void){
	uint8_t addr[8];
  radio_value_t rv;

	rf2xx_driver.get_object(RADIO_PARAM_64BIT_ADDR, &addr, 8);
	printf("Device ID: ");
	for(int j=0; j<8; j++){
		printf("%X",addr[j]);
	}

  printf("\n"); 

  rf2xx_driver.get_value(RADIO_PARAM_CHANNEL, &rv);
  printf("Set on channel %d \n", rv);
	
	printf("----------------------------------------------------------------------------\n");
	printf("\n");
	printf("       DESCRIPTION\n");
	printf("----------------------------------------------------------------------------\n");
	printf("BGN [time-stamp (channel)RSSI] [time-stamp (channel)RSSI] [ ...\n");
	printf("\n");
	printf("Tx [time-stamp] packet-type  dest-addr (chn len sqn | pow) BC or UC \n");
	printf("Rx [time-stamp] packet-type  sour-addr (chn len sqn | rssi lqi) \n");
	printf("\n");
	printf("On the end of file, there is a count of all received and transmitted packets. \n");
	printf("----------------------------------------------------------------------------\n");
}