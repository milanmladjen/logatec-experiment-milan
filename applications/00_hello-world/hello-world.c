/* ----------------------------------------------------------------------------
 * HELLO WORLD APPLICATION
 *
 * Vesna starts with hello_world and prints Hello every second for 1h (default) 
 * ----------------------------------------------------------------------------
*/
#include <stdio.h>
#include "contiki.h"

/*---------------------------------------------------------------------------*/
#define APP_DURATION_IN_SEC    (60 * 60)

/*---------------------------------------------------------------------------*/
PROCESS(hello_world_process, "HelloWorld Process");
AUTOSTART_PROCESSES(&hello_world_process);

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(hello_world_process, ev, data)
{
	static struct etimer timer;
	static uint32_t time_counter = 0;

	PROCESS_BEGIN();

	// Setup a periodic timer that expires after 1 second
	etimer_set(&timer, CLOCK_SECOND );

	time_counter = 0;

	while(1) {
		printf("Hello! \n");

		// If elapsed seconds are equal to APP_DURATION, exit process
		if(time_counter == APP_DURATION_IN_SEC) {
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
