# ----------------------------------------------------------------------
# FILE LOGGER
# ----------------------------------------------------------------------
from datetime import datetime

# ----------------------------------------------------------------------
DEFAULT_FILE_NAME = "node_results.txt"

# ----------------------------------------------------------------------
class file_logger():

    def prepare_file(self, filename, deviceName):
        # Prepare a file and add description to it (date, time)
        self.filename = filename
        self.file = open(filename, mode="w") #, encoding="ASCII") only in python3
        self.file.write(str(datetime.now())+"\n")
        self.file.write("----------------------------------------------------------------------------------------------- \n")
        self.file.write("SERIAL INPUT FROM LGTC DEVICE " + deviceName + "\n")
        self.file.write("----------------------------------------------------------------------------------------------- \n")
        self.file.close()


    def open_file(self):
        self.file = open(self.filename, mode="a") # , encoding="ASCII")

    def store_line(self, data):
        self.file.write("[" + str(datetime.now().time())+"]: ")
        self.file.write(data)

    def store_lgtc_line(self,s):
        self.file.write("[" + str(datetime.now().time())+" LGTC]: ")
        self.file.write(s)

    def warning(self, s):
        self.file.write("[" + str(datetime.now().time())+"] !WARNING!:")
        self.file.write(s)

    def close(self):
        self.ser.close()
        self.file.close()