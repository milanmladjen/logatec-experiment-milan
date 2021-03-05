# Simple database for storing state of devices in the testbed
# {
#     "address":"state"
#
#     "LGTC123":"ONLINE",
#     "LGTC456":"RUNNING",...
# }
# 
# Database is stored to given file (= DATABASE)

import json
import os


class testbed_database():
    
    # Init DB and delete old one if there is any
    def __init__(self, DATABASE):
        self.location = DATABASE
        self.db = {}

        if (os.path.exists(self.location)):
            print("[WARN init] Overwriting old database")
            try:
                f = open(self.location, "w")
                f.write("")
            except:
                print("[ERR init] Can not access database")
            finally:
                f.close()

    def _dumpdb(self):
        try:
            json.dump(self.db, open(self.location, "w+"))
        except:
            print("[ERR] saving database")

    def _cleardb(self):
        try:
            self.db.clear()
            self._dumpdb()
        except:
            print("[ERR] cleaning database")

    def _update(self, addr, state):
        try:
            self.db[addr] = str(state)
            self._dumpdb()
            return True
        except:
            print("[ERR] updating database")
            return False

    def delete(self):
        self._cleardb()
        os.remove(self.location)



    # True if device is the DB, False if not    
    def is_dev(self, addr):
        return (addr in self.db)

    # Remove device from DB
    def remove_dev(self, addr):
        try:
            self.db.pop(addr)
        except:
            print("[ERR remove] %s not in database" % addr)

    # Insert new device to DB
    def insert_dev(self, addr, state):
        if addr in self.db:
            print("[WARN insert] device is allready in database. Updating its state.")
        
        self._update(addr, state)

    # Update the device in DB
    def update_dev_state(self, addr, state):
        if addr in self.db:
            self._update(addr, state)
        else:
            print("[ERR update] %s not in database" % addr)

    # Return the device state stored in the DB
    def get_dev_state(self, addr):
        if addr in self.db:
            return self.db.get(addr)
        else:
            print("[ERR get] %s not in database" % addr)
            return None



    # Return the state of all devices (list of dicts)
    def get_tb_state_json(self):
        j = []
        for dev in self.db:
            j.append( {"address":str(dev),"state":self.db[dev]} )
        return j
    
    # Return the state of all devices (string) - debug purpose
    def get_tb_state_str(self):
        s = ""
        for dev in self.db:
            s += str(dev) + ":" + self.db[dev] + "\n"
        return s
    
    # Return the state of all devices (list of tuples) - not used
    def get_tb_state_list(self):
        return self.db.items()





# Demo usage
if __name__ == "__main__":

    db = testbed_database("test_database.db")

    db.insert_dev("LGTC66", "ONLINE")
    db.insert_dev("LGTC77", "ONLINE")
    db.insert_dev("LGTC88", "ONLINE")

    print("Display testbed state:")
    print(db.get_tb_state_str())
    print(" or ")
    print(db.get_tb_state_list())
    print(" or ")
    print(db.get_tb_state_json())
    print("")

    print("Remove LGTC88:")
    db.remove_dev("LGTC88")

    print("Is LGTC88 active? " + str(db.is_dev("LGTC88") ))

    print("Update LGTC66:")
    db.update_dev_state("LGTC66", "COMPILING")

    print("Device LGTC66 state: " + db.get_dev_state("LGTC66"))

    print("")
    print("Testing incorrect usage:")

    # Incorrect usage - device is not in DB
    db.update_dev_state("LGTC??", "xxx")
    db.get_dev_state("LGTC??")

    # Incorrect usage - adding device which is allready in DB
    db.insert_dev("LGTC66","COMPILING")


    # Optionally delete database file on the end
    db.delete()