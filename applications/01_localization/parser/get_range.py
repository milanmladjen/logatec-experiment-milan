
import sys
import parsed_data as data
import statistics


# To moras rocno poravit 
BREZ_SKRAJNIH = False
MEDIANA = True

# v fajl parsed_data moraš obv dodat naprave, ki so ble neaktivne
# oziroma neso vrnle meritev. Skripta je spisana univerzalno in če ni podatkov
# vrne error. V fajl preprosto dodej: (pazi na št pozicij)
"""
node_xy=[
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
]
"""
try:
    aktivne_naprave = [
        data.node_51,
        data.node_52,
        data.node_53,
        data.node_54,
        data.node_55,
        data.node_56,
        data.node_57,
        data.node_58,
        data.node_59,
        data.node_60,
        data.node_61,
        data.node_62,
        data.node_63,
        data.node_64,
        data.node_65,
        data.node_66,
        data.node_67,
        data.node_68,
        data.node_69,
        data.node_70,
        data.node_71,
        data.node_81,
        data.node_82,
        data.node_83,
        data.node_84,
        data.node_85,
        data.node_86
    ]
except:
    print("Nekatere izmed naprav ni v fajlu parsed_data.py")
    print("Aborting :(")
    sys.exit(1)

ime_naprave = [
    "LGTC51",
    "LGTC52",
    "LGTC53",
    "LGTC54",
    "LGTC55",
    "LGTC56",
    "LGTC57",
    "LGTC58",
    "LGTC59",
    "LGTC60",
    "LGTC61",
    "LGTC62",
    "LGTC63",
    "LGTC64",
    "LGTC65",
    "LGTC66",
    "LGTC67",
    "LGTC68",
    "LGTC69",
    "LGTC70",
    "LGTC71",
    "LGTC81",
    "LGTC82",
    "LGTC83",
    "LGTC84",
    "LGTC85",
    "LGTC86"
]




out_file = open("range.js", mode="w")

out_file.write("var position_measurements = [ \n")

min_dev = 30
max_dev = 0

# Loop skozi pozicije
for pozicija in range(0, len(aktivne_naprave[0])):

    # Loop skozi meritve vsake naprave na tej poziciji
    out_file.write("[\n")
    for node in range(0, len(aktivne_naprave)):
        out_file.write('\t{node: "'+ ime_naprave[node])

        meritve = aktivne_naprave[node][pozicija]
        if not meritve:
            out_file.write('", rssi: [0,0')
        else:
            if(len(meritve) > 2):
                if(MEDIANA):
                    med = statistics.median(meritve)
                    dev = statistics.stdev(meritve)

                    if (dev == 0):
                        print("sfrasdf")

                    #print("MED: " + str(med) + " DEV: " + str(dev))
                    #najvecja = round(med + dev, 1)
                    #najmanjsa = round(med - dev, 1)
                    najmanjsa = med
                    najvecja = round(dev, 2)

                    if(dev < min_dev):
                        min_dev = dev  

                    if (dev > max_dev):
                        max_dev = dev


                # Če zeliš loh odstraniš tiste mejne vrednosti
                # največji max pa največji minimum
                elif (BREZ_SKRAJNIH):
                    meritve.remove(max(meritve))
                    meritve.remove(min(meritve))
                    najvecja = max(meritve)
                    najmanjsa = min(meritve)

                else:
                    najvecja = max(meritve)
                    najmanjsa = min(meritve)
            else:
                #najvecja = max(meritve)
                #najmanjsa = min(meritve)
                najvecja = 0
                najmanjsa = 0


            # Finta da niso iste meritve
            if(najvecja == najmanjsa):
                print("Lokacija: " + str(pozicija +1) + " -- naprava: " + ime_naprave[node] + " ima isti MIN in MAX")

                najmanjsa -= 3
                najvecja += 3

            out_file.write('", rssi: [' + str(najmanjsa) + "," + str(najvecja))
            

        out_file.write("]},\n")

    out_file.write("],\n")

print("ST pozicij: " + str(pozicija+1) + " in st naprav " + str(node+1))

print("Minimalna decviacija = " + str(min_dev))
print("Maximalna decviacija = " + str(max_dev))

out_file.write("];")
