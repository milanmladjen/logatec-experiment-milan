/* -----------------------------------------------------------------------------
 * TEST APPLICATION - TESTBED EXPERIMENT CONTROLLER DEMO
 *
 *
 * -----------------------------------------------------------------------------
*/

#include <stdio.h>
#include <stdlib.h>
#include "contiki.h"
#include "../../contiki-ng/os/net/routing/routing.h"
#include "dev/serial-line.h"

// For detecting RPL network (RPL-specific commands)
#if ROUTING_CONF_RPL_LITE
#include "net/routing/rpl-lite/rpl.h"
#elif ROUTING_CONF_RPL_CLASSIC
#include "net/routing/rpl-classic/rpl.h"
#endif

/*---------------------------------------------------------------------------*/
#define SECOND						(1000)
#define DEFAULT_APP_DUR_IN_SEC		(60 * 60)

uint32_t app_duration = DEFAULT_APP_DUR_IN_SEC;
uint8_t device_in_rpl_network = 0;

/*---------------------------------------------------------------------------*/
PROCESS(experiment_process, "Experiment process");
PROCESS(serial_input_process, "Serial input command");
AUTOSTART_PROCESSES(&serial_input_process);

/*---------------------------------------------------------------------------*/
void input_command(char *data);
void set_device_as_root(void);

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
	char arg[8];
	char *p;

	// Possible commands
	const char carg1[] = "SET_ROOT";
	const char carg2[] = "SOMEVAL";

    switch(cmd){
		// SYNC cmd
		case '@':
			printf("@ \n");
			break;

		// START cmd	
		case '>':
			process_start(&experiment_process, NULL);
			break;

		// STOP cmd
		case '=':
			printf("= Application stopped.\n");
			process_exit(&experiment_process);
			break;

		// APP DURATION
		case '&':
			p = data + 1;
			strcpy(arg, p);
			app_duration = atoi(arg);
			printf("Received app duration %ld \n", app_duration);
			break;

		// COMAND
		case '*':
			p = data + 1;
			printf("Received command %s \n", p);
			strcpy(arg, p);

			if(strcmp(arg, carg1) == 0){
				set_device_as_root();
			}
			else if(strcmp(arg, carg2) == 0){
				printf("* Some value is 10 \n");
			}
			else{
				printf("* Unsupported command: %s \n", p);
			}
			break;

		default:
			printf("Unknown cmd \n");
			break;
    }
}

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(experiment_process, ev, data)
{
	static struct etimer timer;
	static uint32_t time_counter = 0;

	PROCESS_BEGIN();

	// Send start command ('>') back to LGTC so it knows we started the experiment
	printf("> Application started!\n");

	// Setup a periodic timer that expires after 1 second
	etimer_set(&timer, SECOND);

	time_counter = 0;

	while(1) {

		printf("Hello there %ld!\n", time_counter);

		if((curr_instance.used) && (device_in_rpl_network != 1)){
			// TODO: What if devices exits network?
			printf("* joined RPL network \n");
			device_in_rpl_network = 1;
		}

		// If elapsed seconds are equal to APP_DURATION, exit process
		if(time_counter == app_duration) {
			printf("= \n");	// Send stop command ('=') to LGTC
			PROCESS_EXIT();
		}

		// Wait for the periodic timer to expire and then restart the timer
		PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&timer));
		etimer_reset(&timer);

		// Second has passed
		time_counter++;
	}

	PROCESS_END();
}

/*---------------------------------------------------------------------------*/
void
set_device_as_root(void){
	if(!NETSTACK_ROUTING.node_is_root()) {
		NETSTACK_ROUTING.root_start();
		printf("* device is now DAG root\n");
	} else {
		printf("* device is already a DAG root\n");
	}
}
