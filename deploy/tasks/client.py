import socket
import sys
from os import path
s=socket.socket()

host="193.2.205.19"  #IP address of the server
port=50000

print("Connect to server")
try:
	s.connect((host,port))

except socket.gaierror as err:
	print("Address-related error connecting to server: ", err)
	sys.exit(1)

except socket.error as err:
	print("Connection error: ", err)
	sys.exit(1)

#TODO change this path to default solution
filename= path.relpath("/root/LOG-a-TEC-testbed/applications/stats-app/node_results.txt")
f=open(filename, "rb")  #with open (filename, "rb") as f:
line=f.read(1024)
while(line):
	s.send(line)
	#print('sent' , repr(line))
	line=f.read(1024)
f.close()

print("Done sending file to server.")

s.close()
