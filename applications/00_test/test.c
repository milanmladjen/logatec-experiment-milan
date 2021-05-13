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
	
    char cmd_sign = data[0];
	char cmd[6];
	char arg[6];
	char *p;

	// Possible commands:
	// 5 characters reserved for commands, other 5 reserved for arguments
	const char cmd_1[] = "START";
	const char cmd_2[] = "STOP";
	const char cmd_3[] = "ROOT";
	const char cmd_4[] = "DURAT";
	const char cmd_5[] = "VAL";

	switch(cmd_sign){
		// SYNC command
		case '@':
			printf("@ \n");
			break;

		// COMMANDS
		case '$':
			// Get command 
			p = data + 2;
			memcpy(cmd, p, 5);
			cmd[5] = '\0';

			// Get argument
			p = data + 7;
			memcpy(arg, p, 5);
			arg[5] = '\0';

			// $ START
			if(strcmp(cmd, cmd_1) == 0){
				process_start(&experiment_process, NULL);
			}
			// $ STOP
			else if(strcmp(cmd, cmd_2) == 0){
				printf("$ STOP\n");
				process_exit(&experiment_process);
			}
			// $ ROOT
			else if(strcmp(cmd, cmd_3) == 0){
				set_device_as_root();
			}
			// $ DURRA360
			else if(strcmp(cmd, cmd_4) == 0){
				app_duration = atoi(arg);
				printf("Received app duration %ld \n", app_duration);
			}
			// $ VAL
			else if(strcmp(cmd, cmd_5) == 0){
				printf("$ Some value is 10 \n");
			}
			else{
				printf("$ Unsupported command: %s \n", p);
			}

			break;
	}
}

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(experiment_process, ev, data)
{
	static struct etimer timer;
	static uint32_t time_counter = 0;

	PROCESS_BEGIN();

	// Send ACK back to LGTC so it knows we started the experiment
	printf("$ START\n");

	// Setup a periodic timer that expires after 1 second
	etimer_set(&timer, SECOND);

	time_counter = 0;

	while(1) {

		printf("Hello there %ld!\n", time_counter);

		if((curr_instance.used) && (device_in_rpl_network != 1)){
			// TODO: What if devices exits network?
			printf("$ JOINED\n");
			device_in_rpl_network = 1;
		}

		// If elapsed seconds are equal to APP_DURATION, exit process
		if(time_counter == app_duration) {
			printf("$ END\n");	// Send stop command ('=') to LGTC
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
		printf("$ ROOT\n");
	} else {
		printf("$ Device is already a DAG root\n");
	}
}
