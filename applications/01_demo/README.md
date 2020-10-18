# Demo application

The most basic version of application to work with in testbed.
LGTC can control Vesna over serial connection with 4 implemented commands:

* \> will start the application
* = will stop the application
* \* will set device as the root of the network
* & [sec] will set the duration of the application in seconds

## hello-world.c

Vesna starts with *serial_input_process*, which will wait for incoming command from LGTC. When it receives \> command, it wil begin with *log_process*, which can send desired statistics to the LGTC to store.
Application will run for a defined time, then it will sed the stop command (=) to the LGTC and stop its execution.

## serial_monitor.py

Will store everything that it gets on serial connection and store it into a file. Usage:
> python3 serial_monitor.py

Optional arguments:
* -o : set the output file name (if no arguments are given, store it to default *DEFAULT_FILE_NAME*)
* -p : port on which your Vesna is connected (if no arguments are given, monitor will try to find it automatically)
* -r : set device as root of the network

### Detailed

LGTC can control the duration of the application. Time is given either with testbed deployment system as environmental variable or it can be defined by the user. \
When monitor sends start command (\>) to start the application it waits to receive response from Vesna. If there is no response, monitor will try again and in afterwards exit the execution. \
Than it listens on the serial port and stores everything that comes in from Vesna. When it receives stop command (=) it will exit its execution. If Vesna stops responding (in case of an error in application), monitor has build in mechanism to detect that and store the received data anyways.