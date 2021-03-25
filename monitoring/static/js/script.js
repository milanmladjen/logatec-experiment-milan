// ------------------------------------------------------------------------------------------------------------
// Global variables
// ------------------------------------------------------------------------------------------------------------

var tx_msg_nbr = 0;
var rx_msg_nbr = 0;

var experiment_started = 0;

var available_devices = [];



// ------------------------------------------------------------------------------------------------------------
// Testbed tloris animation
// ------------------------------------------------------------------------------------------------------------

class Nodes {

    constructor(){
        this.testbed_devices = [
            // SRDA
            {name:"LGTC51", address:"192.168.12.51", location:1, version:"SRDA"},
            {name:"LGTC52", address:"192.168.12.52", location:2, version:"SRDA"},
            {name:"LGTC53", address:"192.168.12.53", location:3, version:"SRDA"},
            {name:"LGTC54", address:"192.168.12.54", location:4, version:"SRDA"},
            {name:"LGTC55", address:"192.168.12.55", location:5, version:"SRDA"},
            {name:"LGTC56", address:"192.168.12.56", location:6, version:"SRDA"},
            {name:"LGTC57", address:"192.168.12.57", location:7, version:"SRDA"},
            {name:"LGTC58", address:"192.168.12.58", location:9, version:"SRDA"},
            {name:"LGTC59", address:"192.168.12.59", location:11, version:"SRDA"},
            {name:"LGTC60", address:"192.168.12.60", location:13, version:"SRDA"},
            {name:"LGTC61", address:"192.168.12.61", location:15, version:"SRDA"},
            {name:"LGTC62", address:"192.168.12.62", location:16, version:"SRDA"},
            {name:"LGTC63", address:"192.168.12.63", location:18, version:"SRDA"},
            {name:"LGTC64", address:"192.168.12.64", location:19, version:"SRDA"},
            {name:"LGTC65", address:"192.168.12.65", location:20, version:"SRDA"},
            {name:"LGTC66", address:"192.168.12.66", location:21, version:"SRDA"},
            {name:"LGTC67", address:"192.168.12.67", location:22, version:"SRDA"},
            {name:"LGTC68", address:"192.168.12.68", location:23, version:"SRDA"},
            {name:"LGTC69", address:"192.168.12.69", location:24, version:"SRDA"},
            {name:"LGTC70", address:"192.168.12.70", location:25, version:"SRDA"},
            {name:"LGTC71", address:"192.168.12.71", location:26, version:"SRDA"},
        
            // SRDB
            {name:"LGTC81", address:"192.168.12.81", location:1, version:"SRDB"},
            {name:"LGTC82", address:"192.168.12.82", location:2, version:"SRDB"},
            {name:"LGTC83", address:"192.168.12.83", location:3, version:"SRDB"},
            {name:"LGTC84", address:"192.168.12.84", location:4, version:"SRDB"},
            {name:"LGTC85", address:"192.168.12.85", location:5, version:"SRDB"},
            {name:"LGTC86", address:"192.168.12.86", location:6, version:"SRDB"},
            {name:"LGTC87", address:"192.168.12.87", location:7, version:"SRDB"},
            {name:"LGTC88", address:"192.168.12.88", location:9, version:"SRDB"},
            {name:"LGTC89", address:"192.168.12.89", location:11, version:"SRDB"},
            {name:"LGTC90", address:"192.168.12.90", location:13, version:"SRDB"},
            {name:"LGTC91", address:"192.168.12.91", location:15, version:"SRDB"},
            {name:"LGTC92", address:"192.168.12.92", location:16, version:"SRDB"},
            {name:"LGTC93", address:"192.168.12.93", location:18, version:"SRDB"},
            {name:"LGTC94", address:"192.168.12.94", location:19, version:"SRDB"},
            {name:"LGTC95", address:"192.168.12.95", location:20, version:"SRDB"},
            {name:"LGTC96", address:"192.168.12.96", location:21, version:"SRDB"},
            {name:"LGTC97", address:"192.168.12.97", location:22, version:"SRDB"},
            {name:"LGTC98", address:"192.168.12.98", location:23, version:"SRDB"},
            {name:"LGTC99", address:"192.168.12.99", location:24, version:"SRDB"},
            {name:"LGTC100", address:"192.168.12.100", location:25, version:"SRDB"},
            {name:"LGTC101", address:"192.168.12.101", location:26, version:"SRDB"},
        
            // LPWA
            {name:"LGTC111", address:"192.168.12.111", location:1, version:"LPWA"},
            {name:"LGTC112", address:"192.168.12.112", location:6, version:"LPWA"},
            {name:"LGTC113", address:"192.168.12.113", location:20, version:"LPWA"},
            {name:"LGTC114", address:"192.168.12.114", location:27, version:"LPWA"},
        
            // UWB
            {name:"LGTC141", address:"192.168.12.141", location:1, version:"UWB"},
            {name:"LGTC142", address:"192.168.12.142", location:2, version:"UWB"},
            {name:"LGTC143", address:"192.168.12.143", location:3, version:"UWB"},
            {name:"LGTC144", address:"192.168.12.144", location:4, version:"UWB"},
            {name:"LGTC145", address:"192.168.12.145", location:5, version:"UWB"},
            {name:"LGTC146", address:"192.168.12.146", location:6, version:"UWB"}
        ];
        
        // Locations
        this.SRDA_loc = [1, 2, 3, 4, 5, 6, 7, 9, 11, 13, 15, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26];
        this.SRDB_loc = [1, 2, 3, 4, 5, 6, 7, 9, 11, 13, 15, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26];
        this.UWB_loc  = [1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 17];
        this.LPWA_loc = [1, 6, 20, 27];

        // Colors of each state
        this.state_colors = [
            {state:"ONLINE", color:"black"},
            {state:"COMPILING", color:"yellow"},
            {state:"RUNNING", color:"green"},
            {state:"END", color:"orange"},
            {state:"STOPPED", color:"red"},
            {state:"OFFLINE", color:"white"}
        ]
    }


    _get_dev_loc(n){
        for (var i=0; i<this.testbed_devices.length; i++){
            if (this.testbed_devices[i].name == n){
                return this.testbed_devices[i].location;
            }
        }
        console.warn("No location for device " + n);
    }

    _get_dev_ip(n){
        for (var i=0; i<this.testbed_devices.length; i++){
            if (this.testbed_devices[i].name == n){
                return this.testbed_devices[i].address;
            }
        }
        console.warn("No IP for device " + n);
    }

    _get_state_color(s){
        for (var i=0; i<this.state_colors.length; i++){
            if(this.state_colors[i].state == s){
                return this.state_colors[i].color;
            }
        }
        console.warn("No color for state " + s);
    }



    remove_dev(name){
        //document.getElementById("node_" + this._get_dev_loc(name)).style.display = "none";
        $("node_" + this._get_dev_loc(name)).css("display", "none");
    }

    remove_all(){
        for(let i=1; i<28; i++){
            //document.getElementById("node_" + i).style.display = "none";
            $("node_" + i).css("display", "none");
        }
    }

    update_dev(name, state){
        //document.getElementById("node_" + this._get_dev_loc(name)).style.color = this._get_state_color(state);
        $("node_" + this._get_dev_loc(name)).css("display", "block");
        $("node_" + this._get_dev_loc(name)).css("color", this._get_state_color(state));
    }
}


// ------------------------------------------------------------------------------------------------------------
// Dropdown menu manipulation
// ------------------------------------------------------------------------------------------------------------

class Dropdown_menu {

    constructor(){
        this.dd = $("#select_device");
    }

    add_dev(dev){
        // Create new option (value = dd_LGTC66) because id LGTC66 is used elsewhere
        this.dd.append($("<option>").val("dd_" + dev).text(dev));
    }

    remove_dev(dev){
        $("#select_device option[value = 'dd_" + dev + "']").remove();
    }

    remove_all(){
        $("#select_device option[value != 'All']").remove();
    }

}



// Check if input command is in list of supported commands
function commandSupported(c){
    var system_commands = [
        "SYNC_WITH_VESNA",
        "FLASH",
        "STATE",
        "EXIT",
        "START_APP",
        "STOP_APP",
        "RESTART_APP"
    ];

    var app_commands = [
        "LINES",
        "SEC"
        //CONTIKI
    ]

    if(system_commands.includes(c)){
        return 0;
    }
    else if(app_commands.includes(c)){
        return 1;
    }
    else{
        return -1;
    }
}


// ------------------------------------------------------------------------------------------------------------
// Document ready
// ------------------------------------------------------------------------------------------------------------
$(document).ready(function(){

    var tloris = new Nodes();
    var dropdown = new Dropdown_menu();

    // Delete old output logs
    $("#output_field").val("");

    // Remove all nodes from tloris
    tloris.remove_all();

   
    // --------------------------------------------------------------------------------------------------------
    // Web Sockets and its handlers
    // --------------------------------------------------------------------------------------------------------

    // If websocket are on the same domain
    // var socket = io();

    // For different domain, WebSocket server (flask_server.py) must have CORS enabled 
    // https://socket.io/docs/v3/client-initialization/
    var socket = io({path: "/controller/socket.io"});


    socket.on("after connect", function(msg){
        console.log("Successfully connected to server! Is experiment running?: ", msg.data);
        // Update testbed state on connect/reconnect
        if(msg.data == "True"){
            experiment_started = 1;
            socket.emit("testbed update");
        }
    });

    socket.on("experiment started", function(msg){
        console.log("Experiment has started");

        experiment_started = 1;

        // Clear output filed in case something is here from before
        $("#output_field").val("");
        tloris.hide_all();

        socket.emit("testbed update");
    });

    socket.on("experiment stopped", function(msg){
        console.log("Experiment has stopped");

        experiment_started = 0;
        available_devices = [];
        alert("Experiment stopped!")

    });

    socket.on("command response", function(msg){
        console.log("Received response [" + msg.count +"] from device: " + msg.device +" :" + msg.data);

        var formated_msg = "[" + msg.count + "] " + msg.device + ":" + msg.data + "\n";

        // Append text into textarea (don't delete old one)
        $("#output_field").val( $("#output_field").val() + formated_msg);
        // Scroll to bottom
        $("#output_field").scrollTop( $("#output_field")[0].scrollHeight);
    });

    socket.on("device state update", function(msg){
        
        // If this address appears for the first time, add it to dropdown and state list
        var lgtc = msg.data;
        if (available_devices.indexOf(lgtc.address) < 0){
            console.log("Nev available device in testbed");
            available_devices.push(lgtc.address);
            dropdown.add_dev(lgtc.address);
        }
        tloris.update_dev(lgtc.address, lgtc.state)

    });

    socket.on("testbed state update", function(msg){
        console.log("Update whole testbed state.");

        // cycle through received list 
        for(let elmnt of msg.data){

            // If this address appears for the first time, add it to dropdown and state list
            var dev = elmnt.address;
            if (available_devices.indexOf(dev) < 0){
                console.log("Nev available device in testbed");
                available_devices.push(dev);
                dropdown.add_dev(dev);
            }
            tloris.update_dev(lgtc.address, lgtc.state)

            // TODO: Delete devices from the list if they are not in database
            // Remove all on beginning and add new later??
        }

        // TODO: make it a function and do:
        // msg.data.forEach(function);
        // This will call a "function" for each element in list
        
    });

    // --------------------------------------------------------------------------------------------------------
    // Buttons
    // --------------------------------------------------------------------------------------------------------

    $("#send_cmd").on("click", function(event){

        if (experiment_started == 0){
            alert("No active experiment in the testbed");
            return false;
        }
        
        // Get command and check if it is supported
        var nbr;
        var cmd = $("#input_cmd").val();
        var sup = commandSupported(cmd);       
        if(sup < 0){
            alert("Command not supported!")
            return false;
        }
        // If this is a SYSTEM command
        else if (sup == 0){
            nbr = "-1";
        }
        // If it is command for the app, get global message number
        else{
            tx_msg_nbr += 1;
            nbr = tx_msg_nbr.toString();
        }

        // Check which device is selected from dropdown list
        var dev = "";
        dev_list = $("select_device");
        if(dev_list.selectedIndex == 0){
            alert("Please select device!");
            return false;
        }
        else {
            dev = dev_list.options[dev_list.selectedIndex].text;
        }

        console.log("Send command [" + nbr + "] to device: " + dev );
        
        // Send it to server
        socket.emit("new command", {
            device: dev,
            count: nbr,
            data: cmd
        });
        return false;
    });

    // TODO On Enter press, send CMD
    $("#input_cmd").on("keyup", function(e){
        if(e.key === "Enter"){
            console.log("Enter pressed");
        }
    });




// Button to clear output text
    $("#clear_output").on("click", function(event){
        console.log("Clear output");
        $("#output_field").val("");
    });

// Button to update testbed state
    $("#update_testbed").on("click", function(event){

        /*if (experiment_started == 0){
            alert("No active experiment in the testbed");
            return false;
        }*/
        // TODO: for testing...uncomment later

        console.log("Send request to update testbed state");
        socket.emit("testbed update");
    });

});






