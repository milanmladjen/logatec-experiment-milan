
import sys

FIRST_POSITION = "L1S"
LAST_POSITION = "L26E"

base = "node_results_"

out_file = open(("parsed_data.py"), mode="w")

for node in range(51, 87):
    try:
        in_file = open((base + str(node) + ".txt"), mode="r")
    except:
        continue   

    lines = in_file.readlines()

    start = False
    number = 1
    position_s = "L" + str(number) + "S"
    position_e = "L" + str(number) + "E"

    out_file.write("node_" + str(node) + "=[\n")
    for line in lines:

        # If found START position, start storing msmnts
        if position_s in line:
            out_file.write("[")
            start = True
        
        # If end position in the line, end storing
        elif position_e in line:
            #print(line)
            number += 1

            position_s = "L" + str(number) + "S"
            position_e = "L" + str(number) + "E"
            out_file.write("],\n")     
            start = False

            # If last position
            if LAST_POSITION in line:
                break

        # Do nothing until START position found 
        if start:
            # then get msmnts
            if "RSSI " in line:
                word = line.split(" ")
                msmnt = (word[5])
                msmnt = msmnt.replace("{","")
                msmnt = msmnt.replace("}", ",")
                out_file.write(msmnt)

    out_file.write("]\n\n\n")
    print("Stevilo lokacij: " + str(number-1))