# Hello World application

Example of application with Contiki-NG Operating System.

**NOTE:** Duration of the application must be the same in hello-world.c and serial_monitor.py.

## hello-world.c

Vesna will print *Hello!* every second for a defined time *APP_DURATION_IN_SEC*. 

## serial_monitor.py

Will just store everything that it gets on serial connection and store it into a file. Usage:
> python3 serial_monitor.py

Optional arguments:
* -o : set the output file name (if no arguments are given, store it to default *DEFAULT_FILE_NAME*)
* -p : port on which your Vesna is connected (if no arguments are given, monitor will try to find it automatically)