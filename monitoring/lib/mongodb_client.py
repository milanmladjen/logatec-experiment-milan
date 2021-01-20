import pymongo

class mongodb_client():

    def __init__(self, COLLECTION, DATABASE="experiment-monitor", HOST="localhost:27017/"):
        # Connect to MongoDB database
        mongo = pymongo.MongoClient()
        #mongo = pymongo.MongoClient("mongodb://" + HOST)

        # Create/open database
        db = mongo[DATABASE]
        #print(mongo.list_database_names())

        # If collection exists already from experiment before, delete it, create new one
        collections = db.list_collection_names()
        self.col = db[COLLECTION]

        if COLLECTION in collections:
            print("WARNING: Deleting old collection which had same name!")
            self.col.drop()

        self.col.create_index([("address", pymongo.TEXT)], unique=True)


    # Return true if there is device id database
    def isDeviceActive(self, addr):
        return (self.col.count_documents({"address":addr}) > 0)


    # Return number of active devices
    def countActiveDevices(self):
        return self.col.count_documents({})    


    # Insert new device to collection (var in string format!)
    def insertDevice(self, addr, state):
        dev = {"address":addr, "state":state}
        try:
            self.col.insert_one(dev)
        except:
            print("WARNING: Device " + addr + " is already in the collection!")
            #print(self.col.find_one({"address":addr}))


    # Update device state (input a string!)
    def updateDeviceState(self, addr, state):
        query = {"address":addr}
        newstate = {"$set" : {"state":state}}
        x = self.col.update_one(query, newstate)
        if(x.matched_count == 0):
            print("WARNING: No device with address " + addr + " in DB.")
            print("TODO: Should I create new?")


    # Return the state of device (input a string!)
    def getDeviceState(self, addr):
        dev = self.col.find_one({"address":addr})
        return dev.get("state")


    # Return the state of all devices (list of dicts)
    # [{'address': '66', 'state': 'COMPILING'}, {'address': '77', 'state': 'ONLINE'}]
    def getTestbedState(self):
        tb = []
        for x in self.col.find():
            tb.append( {"address":x.get("address"), "state":x.get("state")} )
        return tb


    # Debug purpose - print the state of all devices
    def printTestbedState(self):
        print("State of all devices in the testbed:")
        for x in self.col.find():
            print("Device: " + x.get("address") + " --> state: " + x.get("state"))


    # Delete collection - delete all active devices
    def deleteCollection(self):
        self.col.drop()




# Demo usage
if __name__ == "__main__":
    print("Main - usage example")

    mdb = mongodb_client("active-devices")

    mdb.printTestbedState()
"""
    mdb.insertDevice("66", "ONLINE")
    mdb.insertDevice("77", "ONLINE")

    mdb.updateDeviceState("66", "COMPILING")

    print("Device 66 state: " + mdb.getDeviceState("66"))

    mdb.printTestbedState()

    testbed = mdb.getTestbedState()
    print(testbed)

    print("")
    print(mdb.isDeviceActive("33"))

    # Testing also INCORECT usage 
    mdb.updateDeviceState("12", "COMPILING")
    mdb.insertDevice("66", "START")
    

    # Delete collection on the end...
    mdb.deleteCollection()

"""


