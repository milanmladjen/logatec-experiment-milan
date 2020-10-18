# Stats-app

Application for measuring 6LoWPAN network statistics. Vesna will store every received or transmitted packet information, obtaining data like:

* Packet type
* Destination / source address
* Channel
* Length of a packet
* Sequence Number
* Power of transmission
* RSSI value at reception

On the end of application, Vesna will also present the overall driver statistics, such as:

* Num. of successful or failed transmissions
* Num. of received and just detected packets
* Count of packet types (Enhanced Beacon, Data packet, Acknowledge) 

Data is collected on the drivers level, therefore it is not interfering with Contiki-NG OS. You can check the rf2xx_stats.c file for more information on that.

**Build on top of the 02_demo-with-reset application. Detailed information on application working can be found there.**
