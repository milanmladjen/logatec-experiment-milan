
var node_locations = [
    [-235,265], // 1
    [-165,265], // 2
    [-235,353], // 3
    [-165,353], // 4
    [-235,441], // 5
    [-165,441], // 6
    [-135,175], // 7
    //[-175,190], 
    [-195,175], // 9
    //[-235,190], 
    [-255,173], // 11
    //[-292,264], 
    [-327,288], // 13
    //[-310,330], 
    [-333,360], // 15
    [-337,408], // 16
    //[-333,433], 
    [-355,478], // 18
    [-435,472], // 19
    [-455,525], // 20
    [-313,538], // 21
    [-203,548], // 22
    [-95 ,530], // 23
    [-95 ,440], // 24
    [-93 ,350], // 25
    [-43 ,198], // 26
    //[-140,490]
];

var node_names = [
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


/**
 * Math
 */
export default class ble_localization {

    constructor() {
        this.P_Tx_dBm = 7.0;
        this.alpha = 3.8;
    }

    WLS_localization(x, y, weights, dist) {
        var z = new Array(x.length).fill(1);
        var w = math.diag(weights);
        var A = [];
        var AT = [];
        var tmp, B;

        A.push(math.multiply(-2.0, x));
        A.push(math.multiply(-2.0, y));
        A.push(z);

        A = math.transpose(math.matrix(A));
        AT = math.transpose(A);

        tmp = math.multiply(AT,w);
        tmp = math.multiply(tmp,A);
        tmp = math.inv(tmp);
        tmp = math.multiply(tmp,AT);
        tmp = math.multiply(tmp, w);

        B = math.multiply(-1, math.add(math.square(x), math.square(y)));
        B = math.add(B, math.square(dist));

        tmp = math.multiply(tmp, B);
        x = tmp._data[0];
        y = tmp._data[1];
        return [x,y,0];
    }

    RSSI_to_distance(rssi){
        var distances = [];
        var d = 0;
        for (let index = 0; index < rssi.length; index++) {
            d = (this.P_Tx_dBm - rssi[index] - 40.05)/(this.alpha*10.0);
            d = math.pow(10.0, d);
            distances.push(d);
        }
        return distances;
    }

    weights_to_locations(weights){
        var x = new Array(weights.length).fill(1);
        var y = new Array(weights.length).fill(1);
        for (let index = 0; index < weights.length; index++) {
            if(weights[index]){
                x[index] = node_locations[index][0];
                y[index] = node_locations[index][1];
            }
        }
        return [x,y];
    }


}

/**
 * Device list with their measurement queues & list of active devices.
 * 
 * queue = [
 *  {device:"LGTC51", data:[1,2,3]},
 *  {device:"LGTC52", data:[1,2,3]},
 *  {device:"LGTC53", data:[]},
 *  .
 *  .
 *  .
 *  {device:"LGTC71", data:[1,2,3]},
 * ]
 * 
 * node_states  = [1, 1, 0, ... , 1]
 */
export class rssi_queue {

    constructor() {
        this.num_of_dev = node_names.length;
        this.queue = [];
        this.node_states = [];
        this.node_active = [];
        this.clean();
    }

    // Cleans the queue and list of active devices.
    // Must be called before/after the experiment start/end!
    clean() {
        this.node_states = new Array(this.num_of_dev).fill(0);
        this.node_active = new Array(this.num_of_dev).fill(0);
        this.queue = new Array(this.num_of_dev).fill(0);
        for(let i=0; i<this.num_of_dev; i++) {
            let q = {device:node_names[i], data:[]};
            this.queue[i] = q;
        }
    }

    // Add measurements to the queue and mark the device as active
    putMeasurement(dev_name, rssi) {
        let index = this.queue.findIndex(m => m.device === dev_name);
        if(index != -1){
            this.queue[index]["data"].push(rssi);
            this.node_active[index] = 1;
        }
        else {
            console.warn("Device with name" + dev_name + " is not suited for this exp.")
        }
    }

    // Get measurements from one device
    getOneMeasurement(dev_name) {
        let index = this.queue.findIndex(m => m.device === dev_name);
        return this.queue[index]["data"];
    }

    // Get all & averaged measurements from the queue
    getAllMeasurements(del = true) {
        let m = new Array(this.num_of_dev).fill(0);
        this.node_states = new Array(this.num_of_dev).fill(0);

        // First check if there is enough measurements
        let count = 0;
        for(let i=0; i<this.num_of_dev; i++) {
            let itm = this.queue[i]["data"].length;
            if (itm != 0){
                count += 1;
            }
        }
        if(count <= 3){
            return;
        }

        // Cycle through device queue
        for(let i=0; i<this.num_of_dev; i++) {
            let avg = 0;
            let items = this.queue[i]["data"].length;
            // Cycle through items (if there are any)
            if (items != 0){
                for(let j=0; j<items; j++) {
                    avg += this.queue[i]["data"][j];
                }
                avg /= items;
                m[i] = avg;
                // Delete old measurements
                if (del == true) this.queue[i]["data"] = [];
                this.node_states[i] = 1;
            }
            else{
                m[i] = 0;
            }
        }
        return m; 
    }

    getActiveDevices() {
        return this.node_active;
    }

    getActiveMeasurements() {
        return this.node_states;
    }

    // Debug ... TODO: delete 
    printQueue(){
        console.log(this.queue);
    }
}


// 21 pozicij 
var position_measurements = [ 
    [
        {node: "LGTC51", rssi: [-95.1,-83.9]},
        {node: "LGTC52", rssi: [-89.5,-78.5]},
        {node: "LGTC53", rssi: [-101.2,-90.8]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-100.0,-92.0]},
        {node: "LGTC56", rssi: [-100.2,-91.8]},
        {node: "LGTC57", rssi: [-93.4,-82.6]},
        {node: "LGTC58", rssi: [-96.3,-83.7]},
        {node: "LGTC59", rssi: [-90.5,-79.5]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-98.7,-90.3]},
        {node: "LGTC63", rssi: [-103.6,-95.4]},
        {node: "LGTC64", rssi: [0,0]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-99.9,-92.1]},
        {node: "LGTC67", rssi: [-100.7,-93.3]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [-93.8,-84.2]},
        {node: "LGTC70", rssi: [-94.1,-85.9]},
        {node: "LGTC71", rssi: [-101.7,-92.3]},
    ],
    [
        {node: "LGTC51", rssi: [-94.8,-81.2]},
        {node: "LGTC52", rssi: [-90.1,-77.9]},
        {node: "LGTC53", rssi: [-102.4,-89.6]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-100.6,-91.4]},
        {node: "LGTC56", rssi: [-100.5,-91.5]},
        {node: "LGTC57", rssi: [-94.2,-81.8]},
        {node: "LGTC58", rssi: [-91.9,-82.1]},
        {node: "LGTC59", rssi: [-90.9,-80.1]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-101.9,-92.1]},
        {node: "LGTC63", rssi: [-104.4,-95.6]},
        {node: "LGTC64", rssi: [0,0]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-97.8,-88.2]},
        {node: "LGTC67", rssi: [-98.8,-89.2]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [-97.7,-88.3]},
        {node: "LGTC70", rssi: [-94.5,-85.5]},
        {node: "LGTC71", rssi: [-99.2,-91.8]},
    ],
    [
        {node: "LGTC51", rssi: [-94.5,-83.5]},
        {node: "LGTC52", rssi: [-89.3,-76.7]},
        {node: "LGTC53", rssi: [-101.5,-90.5]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-100.7,-91.3]},
        {node: "LGTC56", rssi: [-100.1,-91.9]},
        {node: "LGTC57", rssi: [-96.0,-86.0]},
        {node: "LGTC58", rssi: [-94.9,-85.1]},
        {node: "LGTC59", rssi: [-90.3,-77.7]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-99.6,-92.4]},
        {node: "LGTC63", rssi: [-99.9,-92.1]},
        {node: "LGTC64", rssi: [0,0]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-100.0,-94.0]},
        {node: "LGTC67", rssi: [-100.1,-93.9]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [-96.9,-89.1]},
        {node: "LGTC70", rssi: [-95.0,-85.0]},
        {node: "LGTC71", rssi: [-97.4,-86.6]},
    ],
    [
        {node: "LGTC51", rssi: [-93.8,-80.2]},
        {node: "LGTC52", rssi: [-87.3,-76.7]},
        {node: "LGTC53", rssi: [-98.3,-87.7]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-101.1,-90.9]},
        {node: "LGTC56", rssi: [-98.7,-91.3]},
        {node: "LGTC57", rssi: [-97.5,-86.5]},
        {node: "LGTC58", rssi: [-97.9,-86.1]},
        {node: "LGTC59", rssi: [-94.3,-81.7]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-99.5,-92.5]},
        {node: "LGTC63", rssi: [-106.6,-99.4]},
        {node: "LGTC64", rssi: [0,0]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-103.5,-96.5]},
        {node: "LGTC67", rssi: [-99.8,-92.2]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [-98.0,-88.0]},
        {node: "LGTC70", rssi: [-96.6,-87.4]},
        {node: "LGTC71", rssi: [-100.6,-89.4]},
    ],
    [
        {node: "LGTC51", rssi: [-92.4,-81.6]},
        {node: "LGTC52", rssi: [-86.6,-73.4]},
        {node: "LGTC53", rssi: [-96.1,-87.9]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-98.1,-87.9]},
        {node: "LGTC56", rssi: [-98.5,-87.5]},
        {node: "LGTC57", rssi: [-100.4,-91.6]},
        {node: "LGTC58", rssi: [-99.5,-84.5]},
        {node: "LGTC59", rssi: [-97.2,-86.8]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-100.4,-91.6]},
        {node: "LGTC63", rssi: [-104.3,-95.7]},
        {node: "LGTC64", rssi: [0,0]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-100.3,-91.7]},
        {node: "LGTC67", rssi: [-101.5,-90.5]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [-95.8,-88.2]},
        {node: "LGTC70", rssi: [-92.9,-83.1]},
        {node: "LGTC71", rssi: [-95.5,-84.5]},
    ],
    [
        {node: "LGTC51", rssi: [-89.2,-78.8]},
        {node: "LGTC52", rssi: [-89.5,-76.5]},
        {node: "LGTC53", rssi: [-95.3,-84.7]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-99.0,-89.0]},
        {node: "LGTC56", rssi: [-99.8,-86.2]},
        {node: "LGTC57", rssi: [-103.1,-92.9]},
        {node: "LGTC58", rssi: [-98.4,-87.6]},
        {node: "LGTC59", rssi: [-96.3,-85.7]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-99.0,-91.0]},
        {node: "LGTC63", rssi: [-105.7,-98.3]},
        {node: "LGTC64", rssi: [0,0]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-101.1,-92.9]},
        {node: "LGTC67", rssi: [-98.2,-87.8]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [-96.1,-87.9]},
        {node: "LGTC70", rssi: [-92.0,-82.0]},
        {node: "LGTC71", rssi: [-93.3,-82.7]},
    ],
    [
        {node: "LGTC51", rssi: [-97.9,-88.1]},
        {node: "LGTC52", rssi: [-89.0,-80.0]},
        {node: "LGTC53", rssi: [-95.0,-83.0]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-100.4,-91.6]},
        {node: "LGTC56", rssi: [-96.9,-87.1]},
        {node: "LGTC57", rssi: [-96.8,-89.2]},
        {node: "LGTC58", rssi: [-97.3,-86.7]},
        {node: "LGTC59", rssi: [-97.2,-86.8]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-97.8,-88.2]},
        {node: "LGTC63", rssi: [-104.0,-96.0]},
        {node: "LGTC64", rssi: [0,0]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-100.3,-91.7]},
        {node: "LGTC67", rssi: [-97.2,-88.8]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [-96.6,-89.4]},
        {node: "LGTC70", rssi: [-96.5,-86.5]},
        {node: "LGTC71", rssi: [-96.2,-87.8]},
    ],
    [
        {node: "LGTC51", rssi: [-99.4,-86.6]},
        {node: "LGTC52", rssi: [-90.5,-81.5]},
        {node: "LGTC53", rssi: [-95.5,-84.5]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-97.1,-84.9]},
        {node: "LGTC56", rssi: [-97.7,-86.3]},
        {node: "LGTC57", rssi: [-100.4,-91.6]},
        {node: "LGTC58", rssi: [-97.8,-86.2]},
        {node: "LGTC59", rssi: [-98.0,-88.0]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-98.5,-91.5]},
        {node: "LGTC63", rssi: [-101.7,-94.3]},
        {node: "LGTC64", rssi: [0,0]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-99.5,-90.5]},
        {node: "LGTC67", rssi: [-99.6,-86.4]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [-97.4,-88.6]},
        {node: "LGTC70", rssi: [-93.2,-80.8]},
        {node: "LGTC71", rssi: [-96.7,-84.3]},
    ],
    [
        {node: "LGTC51", rssi: [-97.0,-87.0]},
        {node: "LGTC52", rssi: [-98.5,-85.5]},
        {node: "LGTC53", rssi: [-95.1,-84.9]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-96.3,-83.7]},
        {node: "LGTC56", rssi: [-94.0,-86.0]},
        {node: "LGTC57", rssi: [-101.4,-92.6]},
        {node: "LGTC58", rssi: [-97.4,-86.6]},
        {node: "LGTC59", rssi: [-98.8,-89.2]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-98.4,-89.6]},
        {node: "LGTC63", rssi: [-104.5,-95.5]},
        {node: "LGTC64", rssi: [0,0]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-98.6,-91.4]},
        {node: "LGTC67", rssi: [-97.2,-88.8]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [-89.7,-80.3]},
        {node: "LGTC70", rssi: [-93.7,-84.3]},
        {node: "LGTC71", rssi: [-100.1,-91.9]},
    ],
    [
        {node: "LGTC51", rssi: [-97.1,-86.9]},
        {node: "LGTC52", rssi: [-96.8,-87.2]},
        {node: "LGTC53", rssi: [-92.9,-79.1]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-97.3,-88.7]},
        {node: "LGTC56", rssi: [-95.4,-84.6]},
        {node: "LGTC57", rssi: [-101.0,-92.0]},
        {node: "LGTC58", rssi: [-97.9,-88.1]},
        {node: "LGTC59", rssi: [-99.2,-90.8]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-98.0,-90.0]},
        {node: "LGTC63", rssi: [-103.4,-90.6]},
        {node: "LGTC64", rssi: [0,0]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-97.1,-86.9]},
        {node: "LGTC67", rssi: [-95.7,-86.3]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [-91.9,-78.1]},
        {node: "LGTC70", rssi: [-90.6,-79.4]},
        {node: "LGTC71", rssi: [-99.7,-92.3]},
    ],
    [
        {node: "LGTC51", rssi: [-93.3,-84.7]},
        {node: "LGTC52", rssi: [-96.1,-85.9]},
        {node: "LGTC53", rssi: [-94.2,-83.8]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-96.5,-87.5]},
        {node: "LGTC56", rssi: [-95.4,-85.6]},
        {node: "LGTC57", rssi: [-100.4,-93.6]},
        {node: "LGTC58", rssi: [-97.7,-86.3]},
        {node: "LGTC59", rssi: [-97.8,-88.2]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-98.9,-91.1]},
        {node: "LGTC63", rssi: [-98.1,-92.9]},
        {node: "LGTC64", rssi: [-113,-100]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-99.1,-92.9]},
        {node: "LGTC67", rssi: [-96.2,-87.8]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [-90.8,-81.2]},
        {node: "LGTC70", rssi: [-92.2,-81.8]},
        {node: "LGTC71", rssi: [-100.4,-91.6]},
    ],
    [
        {node: "LGTC51", rssi: [-96.7,-85.3]},
        {node: "LGTC52", rssi: [-97.6,-86.4]},
        {node: "LGTC53", rssi: [-88.0,-78.0]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-94.8,-85.2]},
        {node: "LGTC56", rssi: [-89.2,-78.8]},
        {node: "LGTC57", rssi: [-100.2,-91.8]},
        {node: "LGTC58", rssi: [-99.8,-90.2]},
        {node: "LGTC59", rssi: [-101.0,-93.0]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-97.6,-90.4]},
        {node: "LGTC63", rssi: [-97.9,-90.1]},
        {node: "LGTC64", rssi: [-102.4,-98.6]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-96.5,-89.5]},
        {node: "LGTC67", rssi: [-98.7,-87.3]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [0,0]},
        {node: "LGTC70", rssi: [-96.1,-87.9]},
        {node: "LGTC71", rssi: [-97.7,-90.3]},
    ],
    [
        {node: "LGTC51", rssi: [-99.2,-88.8]},
        {node: "LGTC52", rssi: [-98.6,-87.4]},
        {node: "LGTC53", rssi: [-85.4,-76.6]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-93.5,-80.5]},
        {node: "LGTC56", rssi: [-96.0,-84.0]},
        {node: "LGTC57", rssi: [-99.9,-92.1]},
        {node: "LGTC58", rssi: [-101.9,-92.1]},
        {node: "LGTC59", rssi: [-100.0,-92.0]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-97.7,-88.3]},
        {node: "LGTC63", rssi: [-100.5,-91.5]},
        {node: "LGTC64", rssi: [-103.5,-96.5]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-100.1,-89.9]},
        {node: "LGTC67", rssi: [-95.8,-86.2]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [0,0]},
        {node: "LGTC70", rssi: [-93.7,-80.3]},
        {node: "LGTC71", rssi: [-98.7,-91.3]},
    ],
    [
        {node: "LGTC51", rssi: [-98.8,-89.2]},
        {node: "LGTC52", rssi: [-98.6,-89.4]},
        {node: "LGTC53", rssi: [-90.1,-79.9]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-96.3,-83.7]},
        {node: "LGTC56", rssi: [-89.8,-80.2]},
        {node: "LGTC57", rssi: [-99.8,-92.2]},
        {node: "LGTC58", rssi: [-101.4,-92.6]},
        {node: "LGTC59", rssi: [-97.2,-89.8]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-96.4,-89.6]},
        {node: "LGTC63", rssi: [-102.0,-90.0]},
        {node: "LGTC64", rssi: [-105,-99]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-98.8,-91.2]},
        {node: "LGTC67", rssi: [-97.1,-86.9]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [0,0]},
        {node: "LGTC70", rssi: [-88.5,-77.5]},
        {node: "LGTC71", rssi: [-101.2,-92.8]},
    ],
    [
        {node: "LGTC51", rssi: [-97.3,-86.7]},
        {node: "LGTC52", rssi: [-100.0,-92.0]},
        {node: "LGTC53", rssi: [-98.6,-87.4]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-92.9,-81.1]},
        {node: "LGTC56", rssi: [-91.5,-80.5]},
        {node: "LGTC57", rssi: [-99.8,-92.2]},
        {node: "LGTC58", rssi: [-99.0,-89.0]},
        {node: "LGTC59", rssi: [-100.1,-91.9]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-97.4,-88.6]},
        {node: "LGTC63", rssi: [-100.0,-92.0]},
        {node: "LGTC64", rssi: [-106.9,-96.1]},
        {node: "LGTC65", rssi: [0,0]},
        {node: "LGTC66", rssi: [-99.1,-90.9]},
        {node: "LGTC67", rssi: [-97.2,-88.8]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [0,0]},
        {node: "LGTC70", rssi: [-93.2,-84.8]},
        {node: "LGTC71", rssi: [-99.6,-92.4]},
    ],
    [
        {node: "LGTC51", rssi: [-99.1,-88.9]},
        {node: "LGTC52", rssi: [-99.8,-92.2]},
        {node: "LGTC53", rssi: [-96.5,-87.5]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-92.9,-83.1]},
        {node: "LGTC56", rssi: [-88.3,-75.7]},
        {node: "LGTC57", rssi: [-102.0,-93.0]},
        {node: "LGTC58", rssi: [-101.5,-92.5]},
        {node: "LGTC59", rssi: [-100.0,-92.0]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-96.9,-89.1]},
        {node: "LGTC63", rssi: [-99.1,-90.9]},
        {node: "LGTC64", rssi: [-102.1,-97.9]},
        {node: "LGTC65", rssi: [-103,-101]},
        {node: "LGTC66", rssi: [-96.5,-88.5]},
        {node: "LGTC67", rssi: [-95.8,-86.2]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [0,0]},
        {node: "LGTC70", rssi: [-95.2,-82.8]},
        {node: "LGTC71", rssi: [-100.5,-95.5]},
    ],
    [
        {node: "LGTC51", rssi: [-99.6,-90.4]},
        {node: "LGTC52", rssi: [-98.5,-89.5]},
        {node: "LGTC53", rssi: [-96.5,-85.5]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-93.5,-82.5]},
        {node: "LGTC56", rssi: [-88.6,-79.4]},
        {node: "LGTC57", rssi: [-97.8,-90.2]},
        {node: "LGTC58", rssi: [-99.8,-92.2]},
        {node: "LGTC59", rssi: [-99.1,-90.9]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-97.3,-86.7]},
        {node: "LGTC63", rssi: [-101.0,-91.0]},
        {node: "LGTC64", rssi: [-100.6,-93.4]},
        {node: "LGTC65", rssi: [-105.2,-96.8]},
        {node: "LGTC66", rssi: [-94.5,-85.5]},
        {node: "LGTC67", rssi: [-95.8,-82.2]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [0,0]},
        {node: "LGTC70", rssi: [-93.1,-84.9]},
        {node: "LGTC71", rssi: [-100.9,-93.1]},
    ],
    [
        {node: "LGTC51", rssi: [-100.1,-91.9]},
        {node: "LGTC52", rssi: [-101.7,-90.3]},
        {node: "LGTC53", rssi: [-92.7,-81.3]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-93.8,-82.2]},
        {node: "LGTC56", rssi: [-85.0,-75.0]},
        {node: "LGTC57", rssi: [-100.6,-93.4]},
        {node: "LGTC58", rssi: [-100.5,-91.5]},
        {node: "LGTC59", rssi: [-100.3,-91.7]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-96.7,-87.3]},
        {node: "LGTC63", rssi: [-99.4,-91.6]},
        {node: "LGTC64", rssi: [0,0]},
        {node: "LGTC65", rssi: [-107,-103]},
        {node: "LGTC66", rssi: [-97.8,-88.2]},
        {node: "LGTC67", rssi: [-93.5,-84.5]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [0,0]},
        {node: "LGTC70", rssi: [-94.0,-86.0]},
        {node: "LGTC71", rssi: [-97.8,-88.2]},
    ],
    [
        {node: "LGTC51", rssi: [-99.5,-92.5]},
        {node: "LGTC52", rssi: [-100.6,-91.4]},
        {node: "LGTC53", rssi: [-94.5,-83.5]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-95.4,-84.6]},
        {node: "LGTC56", rssi: [-84.9,-75.1]},
        {node: "LGTC57", rssi: [-101.6,-94.4]},
        {node: "LGTC58", rssi: [-103.4,-90.6]},
        {node: "LGTC59", rssi: [-99.9,-88.1]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-96.2,-87.8]},
        {node: "LGTC63", rssi: [-101.8,-90.2]},
        {node: "LGTC64", rssi: [-99.6,-95.4]},
        {node: "LGTC65", rssi: [-104.6,-101.4]},
        {node: "LGTC66", rssi: [-97.7,-88.3]},
        {node: "LGTC67", rssi: [-94.9,-81.1]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [0,0]},
        {node: "LGTC70", rssi: [-93.3,-84.7]},
        {node: "LGTC71", rssi: [-100.3,-92.7]},
    ],
    [
        {node: "LGTC51", rssi: [-96.4,-89.6]},
        {node: "LGTC52", rssi: [-100.3,-91.7]},
        {node: "LGTC53", rssi: [-98.5,-85.5]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-92.4,-77.6]},
        {node: "LGTC56", rssi: [-89.7,-74.3]},
        {node: "LGTC57", rssi: [-102.6,-95.4]},
        {node: "LGTC58", rssi: [-101.4,-92.6]},
        {node: "LGTC59", rssi: [-98.2,-91.8]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-95.6,-86.4]},
        {node: "LGTC63", rssi: [-98.0,-89.0]},
        {node: "LGTC64", rssi: [-99.9,-94.1]},
        {node: "LGTC65", rssi: [-108.0,-98.0]},
        {node: "LGTC66", rssi: [-95.1,-84.9]},
        {node: "LGTC67", rssi: [-92.8,-81.2]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [0,0]},
        {node: "LGTC70", rssi: [-96.6,-87.4]},
        {node: "LGTC71", rssi: [-98.0,-88.0]},
    ],
    [
        {node: "LGTC51", rssi: [-102.4,-92.6]},
        {node: "LGTC52", rssi: [-99.9,-92.1]},
        {node: "LGTC53", rssi: [-100.7,-88.3]},
        {node: "LGTC54", rssi: [0,0]},
        {node: "LGTC55", rssi: [-90.8,-81.2]},
        {node: "LGTC56", rssi: [-87.3,-76.7]},
        {node: "LGTC57", rssi: [-106.4,-99.6]},
        {node: "LGTC58", rssi: [-101.0,-93.0]},
        {node: "LGTC59", rssi: [-102.6,-91.4]},
        {node: "LGTC60", rssi: [0,0]},
        {node: "LGTC61", rssi: [0,0]},
        {node: "LGTC62", rssi: [-97.9,-88.1]},
        {node: "LGTC63", rssi: [-99.4,-90.6]},
        {node: "LGTC64", rssi: [-103.0,-95.0]},
        {node: "LGTC65", rssi: [-101.2,-92.8]},
        {node: "LGTC66", rssi: [-96.0,-88.0]},
        {node: "LGTC67", rssi: [-94.5,-83.5]},
        {node: "LGTC68", rssi: [0,0]},
        {node: "LGTC69", rssi: [0,0]},
        {node: "LGTC70", rssi: [-98.7,-87.3]},
        {node: "LGTC71", rssi: [-99.0,-93.0]},
    ],
    ];





// Zacnes pri zacetku smetnjaka in po 3 ploscice naprej (2 preskocis)
var position_coordiantes =[
    [1 , -220, -403],   // smetnjak zacetek
    [2 , -220, -394],
    [3 , -220, -385],   // node 51
    [4 , -220, -376],
    [5 , -220, -367],
    [6 , -220, -358],
    [7 , -220, -349],
    [8 , -220, -340],
    [9 , -220, -331],
    [10, -220, -322],
    [11, -220, -313],
    [12, -220, -304],
    [13, -220, -295],   // node 53
    [14, -220, -286],
    [15, -220, -277],
    [16, -220, -268],
    [17, -220, -259],
    [18, -220, -250],
    [19, -220, -241],
    [20, -220, -232],
    [21, -220, -223],
    [22, -220, -214],
    [23, -220, -205],
    [24, -220, -196],   // node 55
    [25, -220, -187],
    [26, -220, -178],   // smetnjak sredina
];

export class ble_fingerprint {

    constructor() {
        this.num_rx_nodes = 27;
        this.num_positions = 26;

        this.weight_rssi_threshold = -79;

        // Queue for las 5 locations with its weight
        this.q_len = 10;
        this.location_q = [];

        // For LPF
        this.old_pos = 0;
    }

    getLocation (rssi){

        //cycle through position measurements and find matching index
        var possible_loc = new Array(this.num_positions).fill(0);
        var match = 0;
        var count = 0;
        var weight = 0;

        console.log(rssi);

        // Calculate weight for incoming measurements
        for(let i=0; i<rssi.length; i++){
            if (rssi[i] != 0){
                weight += 1;
                // better measurements get higher weight)
                if (rssi[i] > this.weight_rssi_threshold){
                    weight +=1;
                    console.log(rssi[i]);
                }
            }
        }

        // Go through all positions (0~10)
        for(let POS=0; POS<this.num_positions; POS++){

            //console.log("POS: " + POS);

            // Go through RX nodes (0~20)
            for(let NODE=0; NODE<this.num_rx_nodes; NODE++){

                //console.log("NODE: " + NODE);

                // If incoming measurement has any value 
                if(rssi[NODE] != 0){
                    let min = position_measurements[POS][NODE]["rssi"][0];
                    let max = position_measurements[POS][NODE]["rssi"][1];
                    
                    // If fingerprints on that node exists
                    if(min != 0 && max != 0){
                        count += 1;
                        // Compare the incoming value with fingerprints
                        if(rssi[NODE] >= min && rssi[NODE] <= max){
                            match += 1;
                        }
                    }
                }
            }

            let accuracy = match / count; 
            possible_loc[POS] = accuracy;
            count = 0;
            match = 0;
            
            //console.log("Possition " + POS + " : " + accuracy);
        }
        console.log("Location possibilities:")
        console.log(possible_loc);
        //console.log(position_measurements[index]);
        
        // Find max probability of a location
        // IF there is more than 1 maximum in possible locations, take the one with highest neighbors
        let max_accuracy = Math.max.apply(Math, possible_loc);
        //console.log("Max accuracy: " + max_accuracy);

        var izbrana ;
        let mozne = [];
        for(let i=0; i<possible_loc.length; i++){
            if(possible_loc[i] == max_accuracy){
                if(i==0){
                    izbrana = possible_loc[i+1];
                }
                else if(i==possible_loc.length-1){
                    izbrana = possible_loc[i-1]
                }
                else{
                    izbrana = (possible_loc[i-1] + possible_loc[i+1]) /2;
                }
                //console.log("pozicija " + i + " szi verjetnostjo " + izbrana);
                mozne.push([i, izbrana]);
            }
        }
        console.log("Promissing locations: ");
        console.log(mozne);
        let len = mozne.length;
        let max_neighbour = 0;
        let index = 0;
        while(len--){
            if(mozne[len][1] > max_neighbour){
                max_neighbour = mozne[len][1];
                index = mozne[len][0];
            }
        }

        //let index = possible_loc.indexOf(Math.max.apply(Math, possible_loc));
        console.log("--- Chosen location: " + index + " with weight: " + weight);
        

        // ------- Calculate weighted average of locations ---------
        // add position with corresponding weight to end of Q
        this.location_q.push([index,weight]);
        
        // Remove old position from the Q
        if(this.location_q.length > this.q_len){
            this.location_q.shift()
        }
        
        // Weighted sum
        let sum = this.location_q[0][0] * this.location_q[0][1];
        let sum_w = this.location_q[0][1];

        for(let i=1; i<this.location_q.length; i++){
            sum += this.location_q[i][0] * this.location_q[i][1]
            sum_w += this.location_q[i][1];
        }

        let weighted_index = sum/sum_w;

        //for(let j=0; j<this.location_q.length; j++){
        //    console.log("Q_loc: " + this.location_q[j][0] + " W: " + this.location_q[j][1]);
        //}

        console.log("Weighted index: " + weighted_index);
        



        // ------------------ LP filter --------------------

        let lp_index = (this.old_pos * 0.8) + (weighted_index * 0.2);

        
        lp_index = Math.round(lp_index);
        console.log("LP index: " + lp_index);

        this.old_pos = lp_index;

        return position_coordiantes[lp_index];
    }
}