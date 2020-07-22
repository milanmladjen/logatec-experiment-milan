import sys
import socket
import os
# from _thread import *
import threading
import re
import sys
import glob

port = 50000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = ""
s.bind((host, port))

s.listen(5)

numnodes = int(os.environ['NODES_NUM'])
print(numnodes)
print('Server listening...')

i = 0


def client_thread(conn, addr):

    ip = addr[0]
    filename = '%s.txt' % ip

    with open(os.path.join("experiment_results/", filename), "wb") as f:
        print('file opened')
        while True:
            data = conn.recv(1024)
            if not data:
                break
            f.write(data)
    f.close()
    print('Done receiving')

    conn.close()

    

if os.path.exists("experiment_results/") is False:
	os.system("mkdir -m777 experiment_results/")
threads = []
totalthreads = 0
while True:
	if totalthreads == numnodes:
		break
	# print(_thread._count())
	conn, addr = s.accept()
	print('Got connection from', addr)
	totalthreads+=1
	t=threading.Thread(target=client_thread, args=(conn,addr))
	threads.append(t)
	t.start()
    # start_new(client_thread, (conn, addr))
for t in threads:
	t.join()
sys.exit()


"""
import socket
import os
import sys

port=50000
s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host=""
s.bind((host,port))
s.settimeout(900)
s.listen(5)

print ('Server listening...')

i=0

while True:
	try:
		conn, addr = s.accept()
		print ('Got connection from' , addr)
		if os.path.exists('node_stats.txt') is True:
			i+=1
			filename='node_stats%s.txt' % i  #filename will be node_stats.txt ===> filename='node_stats%s.txt' % i
		else:
			filename="node_stats.txt"

		with open (filename, "wb") as f:
			print('file opened')
			while True:
				data=conn.recv(1024)
				if not data:
					break
				f.write(data)
		f.close()
		print('Done receiving')
		
		os.system("rm -rf experiment_results")
		os.system("mkdir experiment_results/")
		os.system("mv node_stats* experiment_results/")
		
		# conn.close()
		# sys.exit()

	except socket.timeout as e:
		s.close()
		sys.exit()
"""
