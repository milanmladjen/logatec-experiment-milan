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

// For printing IP address
#include "net/ipv6/uiplib.h"
#include "net/ipv6/uip-ds6.h"
#include "sys/log.h"

// For detecting RPL network (RPL-specific commands)
#if ROUTING_CONF_RPL_LITE
#include "net/routing/rpl-lite/rpl.h"
#elif ROUTING_CONF_RPL_CLASSIC
#include "net/routing/rpl-classic/rpl.h"
#endif

/*---------------------------------------------------------------------------*/
#define SECOND						(1000)
#define DEFAULT_APP_DUR_IN_SEC		(10 * 60)

uint32_t app_duration = DEFAULT_APP_DUR_IN_SEC;

/*---------------------------------------------------------------------------*/
PROCESS(experiment_process, "Experiment process");
PROCESS(serial_input_process, "Serial input command");
PROCESS(check_network_process, "Check network process");
AUTOSTART_PROCESSES(&serial_input_process, &check_network_process);

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
	const char cmd_5[] = "IP";
	const char cmd_5[] = "PAREN";

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
				if(!NETSTACK_ROUTING.node_is_root()) {
					NETSTACK_ROUTING.root_start();
					printf("$ ROOT\n");
				} else {
					printf("$ Device is already a DAG root\n");
				}
			}
			// $ DURRA360
			else if(strcmp(cmd, cmd_4) == 0){
				app_duration = atoi(arg);
				printf("Received app duration %ld \n", app_duration);
			}
			// $ IPADR
			else if(strcmp(cmd, cmd_5) == 0){
				// Print IP address of the device
				#if NETSTACK_CONF_WITH_IPV6
				{
					uip_ds6_addr_t *lladdr;
					char buf[UIPLIB_IPV6_MAX_STR_LEN];
					lladdr = uip_ds6_get_link_local(-1);
					uiplib_ipaddr_snprint(buf, sizeof(buf), &lladdr->ipaddr);

					printf("$ My IP address is:");
					printf(buf);
					printf("\n");
				}
				#endif
			}
			// $ PAREN(t)
			else if(strcmp(cmd, cmd_6) == 0){
				if(!NETSTACK_ROUTING.node_is_root()){
					uip_ipaddr_t *parent_ipaddr;
					char buf[UIPLIB_IPV6_MAX_STR_LEN];
					parent_ipaddr = rpl_parent_get_ipaddr(curr_instance.dag.preferred_parent);
					uiplib_ipaddr_snprint(buf, sizeof(buf), parent_ipaddr);

					printf("$ My parent is:");
					printf(buf);
					printf("\n");
				}
			}
			else{
				printf("$ Unsupported command: %s \n", p);
			}

			break;
	}
}

/*---------------------------------------------------------------------------*/
// Process to check when device enters the RPL network
// It takes some time for a device to give up on the DAG network (3min).
// (cur_instance.used) is still true even when device is allready out of the 
// network, scanning for new parents. Maybe you can use TSCH MAC WARNING:
// "[WARN: TSCH      ] leaving the network stats: xxxxx"
PROCESS_THREAD(check_network_process, ev, data)
{	
	static struct etimer net;
	static uint8_t in_network = 0;

    PROCESS_BEGIN();
	etimer_set(&net, SECOND);

    while(1){
		// If device is in the network
		if(in_network){
			// If device exits the netowrk
			if(!curr_instance.used){
				printf("$ EXIT_DAG\n");
				in_network = 0;
			}
		}
		// If device came to RPL network
		else if(curr_instance.used){
			// If device is not the root
			if(!NETSTACK_ROUTING.node_is_root()){
				printf("$ JOIN_DAG\n");
			}
			in_network = 1;
		}

		PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&net));
		etimer_reset(&net);
    }
    PROCESS_END();
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
