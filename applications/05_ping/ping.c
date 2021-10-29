/* -----------------------------------------------------------------------------
 * APPLICATION FOR PINGING NEIGHBOURS IN THE NETWORK
 * TODO not tested jet - just prepared (copied from last repo)
 * -----------------------------------------------------------------------------
*/

#include "contiki.h"
#include <stdio.h>
#include <stdlib.h>
#include "dev/serial-line.h"
#include "../../contiki-ng/arch/platform/vesna/dev/at86rf2xx/rf2xx_stats.h"
#include "net/ipv6/uip.h"

/*---------------------------------------------------------------------------*/
#define SECOND						(1000)
#define DEFAULT_APP_DUR_IN_SEC		(60 * 60)
#define PING_SEND_TIME		        (3)

// Is device root of the DAG network
static uint8_t device_is_root = 0;

// Varables for ping process
static const char *ping_output_func = NULL;
static struct process *curr_ping_process;
static uint8_t ping_ttl;
static uint16_t ping_datalen;
static uint32_t ping_count = 0;
static uint32_t ping_timeout_count = 0;
static uint32_t ping_time_start;
static uint32_t ping_time_reply;

uint32_t app_duration = DEFAULT_APP_DUR_IN_SEC;

enum STATS_commands {cmd_start, cmd_stop, cmd_appdur};
/*---------------------------------------------------------------------------*/
void STATS_print_description(void);
void STATS_input_command(char *data);
void STATS_output_command(uint8_t cmd);
void STATS_set_device_as_root(void);
void STATS_close_app(void);


void STATS_setup_ping_reply_callback(void);
void ping_reply_handler(uip_ipaddr_t *source, uint8_t ttl, uint8_t *data, uint16_t datalen);

/*---------------------------------------------------------------------------*/
PROCESS(stats_process, "Stats app process");
PROCESS(serial_input_process, "Serial input command");
PROCESS(ping_process, "Pinging process");

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
			break;

		case '*':
			STATS_set_device_as_root();
			break;

		case '=':
			process_exit(&stats_process);
			STATS_close_app();
			break;

		case '&':
			p = data + 1;
			strcpy(time, p);
			app_duration = atoi(time);
			STATS_output_command(cmd_appdur);
			break;

    /*  case '!':
            // Example usage (not tested yet): ! fe80::212:4b00:6:1234
            uip_ipaddr_t remote_addr;
            char *args;
            args = data[2];
            if(uiplib_ipaddrconv(args, &remote_addr) != 0){
                process_start(&ping_process, &remote_addr);
            }
            break;
	*/

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

	STATS_print_description();

	etimer_set(&timer, SECOND);

	while(1) {	

        uip_ds6_nbr_t *nbr;
		uip_ipaddr_t *address;

		if(!device_is_root){
			if((time_counter % PING_SEND_TIME) == 0){

				nbr = uip_ds6_nbr_head();

				if(nbr != NULL){
					//printf("Found nbr at IP:");
					//uiplib_ipaddr_print(uip_ds6_nbr_get_ipaddr(nbr));

					address = uip_ds6_nbr_get_ipaddr(nbr);
					//nbr = uip_ds6_nbr_next(nbr); - if there are more neighbors
					
					process_start(&ping_process, address);
				}
			}
		}

		if((time_counter % 10) == 0){
			STATS_print_packet_stats();
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
    device_is_root = 1;
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

	// Reset the network
	if(NETSTACK_ROUTING.node_is_root()){
		NETSTACK_ROUTING.leave_network();
	}

    device_is_root = 0;
}

/*---------------------------------------------------------------------------*/
void
STATS_print_description(void){
	uint8_t addr[8];
  	radio_value_t rv;

	printf("----------------------------------------------------------------------------\n");
	rf2xx_driver.get_object(RADIO_PARAM_64BIT_ADDR, &addr, 8);
	printf("Device ID: ");
	for(int j=0; j<8; j++){
		printf("%X",addr[j]);
	}
  	printf("\n"); 

#if !MAC_CONF_WITH_TSCH
	rf2xx_driver.get_value(RADIO_PARAM_CHANNEL, &rv);
	printf("Set on channel %d \n", rv);
#endif

	printf("----------------------------------------------------------------------------\n");
	printf("   STATISTICS\n");
	printf("----------------------------------------------------------------------------\n");
	printf("BGN [time-stamp (channel)RSSI] [time-stamp (channel)RSSI] [ ...\n");
	printf("\n");
	printf("Tx [time-stamp] packet-type  dest-addr (chn len sqn | pow) BC or UC \n");
	printf("Rx [time-stamp] packet-type  sour-addr (chn len sqn | rssi lqi) \n");
	printf("\n");
	printf("On the end of file, there is a count of all received and transmitted packets. \n");
	printf("----------------------------------------------------------------------------\n");
}


/*---------------------------------------------------------------------------*/
PROCESS_THREAD(ping_process, ev, data)
{
	static struct etimer timeout_timer;

	PROCESS_BEGIN();

	#if STATS_DEBUGG
		printf("Pinging neighbour: ");
		uiplib_ipaddr_print(data);
		printf("\n"); 
	#endif

	curr_ping_process = PROCESS_CURRENT();
  	ping_output_func = "ping";
	ping_time_start = vsnTime_uptimeMS();
	etimer_set(&timeout_timer, (SECOND));
	uip_icmp6_send(data, ICMP6_ECHO_REQUEST, 0, 4);	//data is the address
	PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&timeout_timer) || ping_output_func == NULL );

	// Timeout
	if(ping_output_func != NULL){
		ping_timeout_count++;
		printf("PT %ld [%ld]\n",ping_timeout_count, ping_time_start);
		ping_output_func = NULL;
	} 
	// Reply received
	else{
		ping_count++;
		printf("PR %ld [%ld - > %ld]\n", ping_count, ping_time_start, ping_time_reply);

		#if STATS_DEBUG
			printf("Received ping reply from ");
			uiplib_ipaddr_print(data);
			printf(", len %u, ttl %u, delay %lu ms\n",
					ping_datalen, ping_ttl, (1000*(clock_time() - timeout_timer.timer.start))/CLOCK_SECOND);
		#endif
	}
	PROCESS_END();
}


void
STATS_setup_ping_reply_callback(void)
{
	static struct uip_icmp6_echo_reply_notification echo_reply_notification;
	uip_icmp6_echo_reply_callback_add(&echo_reply_notification, ping_reply_handler);
}

void
ping_reply_handler(uip_ipaddr_t *source, uint8_t ttl, uint8_t *data, uint16_t datalen)
{
  if(ping_output_func != NULL) {
	ping_time_reply = vsnTime_uptimeMS();
    ping_output_func = NULL;
    ping_ttl = ttl;
    ping_datalen = datalen;

    process_poll(curr_ping_process);
  }
}
