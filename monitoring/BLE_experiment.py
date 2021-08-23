#!/usr/bin/python3

import queue
import threading
from queue import Queue

class BLE_experiment(threading.Thread):

    def __init__(self):
        self._is_thread_running = True

    
    def run(self):

        self.queuePutState("RUNNING")

        # Start advertising

        while self._is_thread_running:

            # Scan BLE interface
            if new_dev:
                self.queuePutInfo("New device found: ...")


            # -------------------------------------------------------------------------------
            # CONTROLLER CLIENT - GET COMMANDS
            # Check for incoming commands for queue - only when there is time 
            if (not self.in_q.empty()):

                sqn, cmd = self.queueGet()

                if cmd == "LINES":
                    resp = "Število vrstic je xy"
                    self.queuePutResp(sqn, resp)


    def stop(self):
        print("Stopping BLE experiment thread")



    # ----------------------------------------------------------------------------------------
    # OTHER FUNCTIONS
    # ----------------------------------------------------------------------------------------
    def queuePutResp(self, sqn, resp):
        self.out_q.put([sqn, resp])

    def queuePutState(self, state):
        self.out_q.put(["STATE", state])

    def queuePutInfo(self, info):
        self.out_q.put(["INFO", info])

    def queueGet(self):
        tmp = self.in_q.get()
        return tmp[0], tmp[1]