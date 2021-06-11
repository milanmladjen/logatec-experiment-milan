/* -----------------------------------------------------------------------------
 * TEST APPLICATION - TESTBED EXPERIMENT CONTROLLER DEMO
 *
 *
 * -----------------------------------------------------------------------------
*/


#include "contiki.h"
#include "sys/node-id.h"
#include "sys/log.h"
#include "net/ipv6/uip-ds6-route.h"
#include "net/ipv6/uip-sr.h"
#include "net/mac/tsch/tsch.h"
#include "net/routing/routing.h"
#include "services/tsch-cs/tsch-cs.h"

#define DEBUG DEBUG_PRINT
#include "net/ipv6/uip-debug.h"

// For serial input
#include <stdio.h>
#include <stdlib.h>
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


// Radio driver statistics
#include "arch/platform/vesna/dev/at86rf2xx/rf2xx.h"
#include "arch/platform/vesna/dev/at86rf2xx/rf2xx_stats.h"

// For channel statistics
#include "tsch-stats.h"


// UDP
#include "random.h"
#include "net/netstack.h"
#include "net/ipv6/simple-udp.h"
#include <inttypes.h>

/*---------------------------------------------------------------------------*/
#define SECOND						(1000)
#define DEFAULT_APP_DUR_IN_SEC		(20 * 60)

uint32_t app_duration = DEFAULT_APP_DUR_IN_SEC;

uint32_t received_responses = 0;


#define UDP_PORT 8214
#define SEND_INTERVAL (2)		// In seconds

static struct simple_udp_connection udp_conn;

// Store up to 20 device address as a list of chars...each addres has 40B reserved
static char device_list[20 * UIPLIB_IPV6_MAX_STR_LEN];
static uint8_t device_count = 0;
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
	const char cmd_6[] = "PAREN";

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
				STATS_display_driver_stats();
				process_exit(&experiment_process);
				if(NETSTACK_ROUTING.node_is_root()){
					NETSTACK_ROUTING.leave_network();
				}
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
					lladdr = uip_ds6_get_link_local(-1);
					printf("$ My IP address is: ");
					uiplib_ipaddr_print(&lladdr->ipaddr);
					printf("\n");
				}
				#endif
			}
			// $ PAREN(t)
			else if(strcmp(cmd, cmd_6) == 0){
				if(!NETSTACK_ROUTING.node_is_root()){
					printf("$ My parent is: ");
					uiplib_ipaddr_print(rpl_parent_get_ipaddr(curr_instance.dag.preferred_parent));
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
static void
udp_rx_callback(struct simple_udp_connection *c,
         const uip_ipaddr_t *sender_addr,
         uint16_t sender_port,
         const uip_ipaddr_t *receiver_addr,
         uint16_t receiver_port,
         const uint8_t *data,
         uint16_t datalen)
{
	uint32_t message;
	memcpy(&message, data, sizeof(uint32_t));

	// Calback if device is root of the network
	if(NETSTACK_ROUTING.node_is_root()){
		if(message == 0){
			printf("New device ");
			uiplib_ipaddr_print(sender_addr);
			printf("\n");

			//memcpy(&device_addr, sender_addr, sizeof(device_addr));

			// Store device ip to the list of devices (as string)
			char buf[40];
			uiplib_ipaddr_snprint(buf, 40, sender_addr);
			memcpy(device_list + (device_count * 40), buf, 40);
			device_count++;
		}
		else{
			printf("$ Received response %"PRIu32" from ", message);
			uiplib_ipaddr_print(sender_addr);
			printf("\n");
		}
	}
	// Calback for normal devices
	else{
		printf("Received request %"PRIu32" from ", message);
		uiplib_ipaddr_print(sender_addr);
		printf("\n");
		printf("Sending response \n");
		simple_udp_sendto(&udp_conn, &message, sizeof(message), sender_addr);
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

	// Initialize UDP connection here, because proces starts at startup
	simple_udp_register(&udp_conn, UDP_PORT, NULL, UDP_PORT, udp_rx_callback);

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

	static uint32_t count = 0;
  	uip_ipaddr_t dest_addr;

	PROCESS_BEGIN();

	// Send ACK back to LGTC so it knows we started the experiment
	printf("$ START\n");

	// Empty statistic buffers if they have some values from before
	RF2XX_STATS_RESET();
	STATS_clear_packet_stats();

	// If device is simple node, register it to the root device
	if(!NETSTACK_ROUTING.node_is_root()){
		while(1){
			if(NETSTACK_ROUTING.node_is_reachable() && NETSTACK_ROUTING.get_root_ipaddr(&dest_addr)) {
				printf("Registering to the root device. \n");
				simple_udp_sendto(&udp_conn, &count, sizeof(count), &dest_addr);
				break;
			}
			else{
				printf("$ Root not reachable yet...waiting 5 seconds. \n");
				etimer_set(&timer, SECOND * 5);
				PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&timer));
			}
		}
	}
	// If device is root, wait 10 seconds before sending request to nodes
	else{
		etimer_set(&timer, SECOND * 10);
		PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&timer));
	}

	// Setup a periodic timer that expires after 1 second
	etimer_set(&timer, SECOND);
	time_counter = 0;

	while(1) {

		// If device is ROOT
		if(NETSTACK_ROUTING.node_is_root()){

			// Every send interval, send packet to a random device
			if((time_counter % SEND_INTERVAL) == 0){
				printf("Sending request to random device: \n");

				char buf[40];
				// Get random device from the list
				memcpy(buf, device_list + ((random_rand() % device_count) * 40), 40);

				if(uiplib_ip6addrconv(buf, &dest_addr)){

					uiplib_ipaddr_print(&dest_addr);
					printf("\n");
					count++;
					simple_udp_sendto(&udp_conn, &count, sizeof(count), &dest_addr);
				}
				else{
					printf("$ Got wrong address \n");
				}
			}

			// Every 10 seconds, print packet statistics
			if((time_counter % 10) == 0){
				STATS_print_driver_stats();
			}
		}
		

		// Every 10 seconds, clear packet buffers (printing them causes delay that we dont want)
		if((time_counter % 10) == 0){
			STATS_clear_packet_stats();
		}
		

		// If elapsed seconds are equal to APP_DURATION, exit process
		if(time_counter == app_duration) {
			STATS_display_driver_stats();
			printf("$ Sent: %ul | received: %ul \n", count, received_responses);
			printf("$ END\n");	// Send stop command ('=') to LGTC
			PROCESS_EXIT();
		}



		PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&timer));
		etimer_reset(&timer);
		time_counter++;	// Second has passed
	}
	PROCESS_END();
}
