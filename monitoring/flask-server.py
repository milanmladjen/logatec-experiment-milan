#   TODO
#   Maybe use socketio threads instead of threading library? (example: https://github.com/shanealynn/async_flask/blob/master/application.py)
#

from threading import Thread, Lock
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import zmq


# Global variable - command in queue, which needs to be sent to LGTC device
# If array is empty that means that no message needs to be sent. 
# Because it is thread shared variable, use lock before using it 
message_to_send = []
lock = Lock()

# Flask and SocketIO config
app = Flask(__name__)
socketio = SocketIO(app)

# ------------------------------------------------------------------------------- #
# Flask
# ------------------------------------------------------------------------------- #

# Store essential values and use it in case of page reload-TODO MongoDB
templateData ={
    "example_string" : "monitor" 
}

@app.route("/")
def index():
    # Use jinja2 template to render html with app values
    return render_template("index.html", **templateData)



# ------------------------------------------------------------------------------- #
# SocketIO
# ------------------------------------------------------------------------------- #
@socketio.on("connect")
def connect():
    print("Client connected")
    emit("after connect",  {"data":"Hello there!"})

@socketio.on("disconnect")
def disconnect():
    print("Client disconnected.")

@socketio.on("new command")
def received_command(cmd):
    print("Client sent: ")
    print(cmd)

    
    # Forward the received command from client browser to the 0MQ broker script
    # Can't send it from here, because 0MQ is in other thread - using 0MQ context
    # in multiple threads may cause problems (it is not thread safe)
    lock.acquire()
    global message_to_send
    message_to_send = [cmd["device"].encode(), cmd["count"].encode(), cmd["data"].encode()] # From dict to byte array
    #print(message_to_send)
    lock.release()

    

def socketio_send_response(resp):
    socketio.emit("command response", resp, broadcast=True)

def socketio_send_status_update():
    socketio.emit("status update", {"data":"update smth"}, broadcast=True)



# ------------------------------------------------------------------------------- #
# Another thread only for receiving messages from 0MQ broker script
# 0MQ communication between 2 processes (IPC transport)
# ------------------------------------------------------------------------------- #
class zmqWorker(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.active = True
        self.context = zmq.Context()
        self.zmq_soc = self.context.socket(zmq.DEALER)
        self.zmq_soc.setsockopt(zmq.IDENTITY, b"flask_process")
        self.zmq_soc.connect("ipc:///tmp/zmq_ipc")

        self.poller = zmq.Poller()
        self.poller.register(self.zmq_soc, zmq.POLLIN)
 
    def run(self):
        

        while self.active:
            
            lock.acquire()
            global message_to_send

            # If there is any message to be sent
            if message_to_send:
                print("Send message to broker!")
                print(message_to_send)
                self.zmq_soc.send_multipart(message_to_send)
                message_to_send = []
                lock.release()

            else:
                lock.release()

                # Check if there is any message for us in queue (reduce it to 100ms or such)
                socks = dict(self.poller.poll(1000))

                if socks.get(self.zmq_soc) == zmq.POLLIN:

                    print("Received message from broker!")

                    device, count, data = self.zmq_soc.recv_multipart()

                    # From bytes to string [device, count, data]
                    msg = [device.decode(), count.decode(), data.decode()]

                    if msg[0] == "all":
                        socketio_send_status_update()
                    
                    else:
                        # Form response in dict
                        response = {
                            "device" : msg[0],
                            "count" : msg[1],
                            "data" : msg[2]
                        }
                        # Forward message to the client over websockets
                        socketio_send_response(response)




if __name__ == '__main__':

    worker = zmqWorker()
    worker.start()

    print("Start the server!")
    socketio.run(app, host='0.0.0.0', debug=False)

