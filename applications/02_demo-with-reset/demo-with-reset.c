/* -----------------------------------------------------------------------------
 * BASIC VERSION OF TESTBED APPLICATION
 *
 * Vesna starts only with serial_input process. When LGTC sends "start" command,
 * which is character '>', Vesna will start with stats_process.
 * If root also sends '*' command, set device as root of the network.
 * -----------------------------------------------------------------------------
*/

#include <stdio.h>
#include <stdlib.h>
#include "contiki.h"
#include "../../contiki-ng/os/net/routing/routing.h"
#include "dev/serial-line.h"

/*---------------------------------------------------------------------------*/
#define SECOND						(1000)
#define DEFAULT_APP_DUR_IN_SEC		(60 * 60)

uint32_t app_duration = DEFAULT_APP_DUR_IN_SEC;

/*---------------------------------------------------------------------------*/
PROCESS(log_process, "Logging process");
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
	char time[8];
	char *p;
    switch(cmd){
		case '>':
			process_start(&log_process, NULL);
			break;

		case '*':
			set_device_as_root();
			break;

		case '=':
			printf("= \n");	// Confirm received stop command
			process_exit(&log_process);
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
PROCESS_THREAD(log_process, ev, data)
{
	static struct etimer timer;
	static uint32_t time_counter = 0;

	PROCESS_BEGIN();

	// Send start command ('>') back to LGTC so it knows we started log_process
	printf("> \n");

	// Setup a periodic timer that expires after 1 second
	etimer_set(&timer, SECOND);

	time_counter = 0;

	while(1) {
		printf("Hello!\n");

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
	} else {
		printf("Node is already a DAG root\n");
	}
}
