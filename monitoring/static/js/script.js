// ------------------------------------------------------------------------------------------------------------
// Global variables
// ------------------------------------------------------------------------------------------------------------

var tx_msg_nbr = 0;
var rx_msg_nbr = 0;

var experiment_running = false;
var available_devices = [];

var SYSTEM_COMMANDS = [
    "START_APP",
    "STOP_APP",
    "RESTART_APP",
    "FLASH",
    "EXIT",
    "STATE"
];


// ------------------------------------------------------------------------------------------------------------
// Testbed tloris animation
// ------------------------------------------------------------------------------------------------------------

class Nodes {

    constructor(){

        // Colors of each state
        this.state_colors = [
            {state:"ONLINE", color:"black"},
            {state:"COMPILING", color:"yellow"},
            {state:"RUNNING", color:"green"},
            {state:"STOPPED", color:"blue"},
            {state:"FINISHED", color:"turquoise"},

            {state:"TIMEOUT", color:"red"},
            {state:"LGTC_WARNING", color:"orange"},
            {state:"COMPILE_ERROR", color:"pink"},
            {state:"VESNA_ERROR", color:"purple"}
        ]

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
        
        // Locations and its radios
        this.SRDA_loc = [1, 2, 3, 4, 5, 6, 7, 9, 11, 13, 15, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26];
        this.SRDB_loc = [1, 2, 3, 4, 5, 6, 7, 9, 11, 13, 15, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26];
        this.UWB_loc  = [1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 17];
        this.LPWA_loc = [1, 6, 20, 27];
    }


    _get_dev_loc(n){
        for (var i=0; i<this.testbed_devices.length; i++){
            if (this.testbed_devices[i].name == n){
                return this.testbed_devices[i].location;
            }
        }
        console.warn("No location for device " + n);
        return 0;
    }

    _get_dev_ip(n){
        for (var i=0; i<this.testbed_devices.length; i++){
            if (this.testbed_devices[i].name == n){
                return this.testbed_devices[i].address;
            }
        }
        console.warn("No IP for device " + n);
        return 0;
    }

    _get_state_color(s){
        for (var i=0; i<this.state_colors.length; i++){
            if(this.state_colors[i].state == s){
                return this.state_colors[i].color;
            }
        }
        console.warn("No color for state " + s);
        return "white";
    }



    remove_dev(name){
        let loc = this._get_dev_loc(name);
        if (loc > 0){
            $("#node_" + loc).css("visibility", "hidden");
        }
    }

    remove_all(){
        for(let i=1; i<28; i++){
            $("#node_" + i).css("visibility", "hidden");
        }
    }

    update_dev(name, state){
        let loc = this._get_dev_loc(name);
        let ip = this._get_dev_ip(name);

        if (loc > 0){
            $("#node_" + loc).css("visibility", "visible");
            $("#node_" + loc).css("color", this._get_state_color(state));
        
            // Update and show tooltip
            // Had problems with updating HTML template - creating new one from scratch
            var new_content = "<table><tr><th>Name: </th><td>" + name + 
            "</td></tr><tr><th>IP: </th><td>" + ip +
            "</td></tr><tr><th>Location: </th><td>" + loc +
            "</td></tr><tr><th>Status: </th><td>" + state +
            "</td></tr></table>";
            
            $("#node_" + loc).tooltipster("content", $((new_content)));
        }
    }

    show_srda_dev(){
        for (let i=0; i<this.SRDA_loc.length; i++){
            $("#node_" + this.SRDA_loc[i]).css("visibility", "visible");
        }
    }
}


// ------------------------------------------------------------------------------------------------------------
// Dropdown menu
// ------------------------------------------------------------------------------------------------------------

class Dropdown_menu {

    constructor(){
        this.dd = $("#select_device");
    }

    add_dev(dev){
        // Create new option (value = dd_LGTC66) because id LGTC66 is used elsewhere (TODO: where??)
        this.dd.append($("<option>").val("dd_" + dev).text(dev));
    }

    remove_dev(dev){
        this.dd.find("option[value = 'dd_" + dev + "']").remove();
    }

    remove_all(){
        this.dd.find("option").not(":first").remove();
        this.dd.append($("<option>").val("All").text("All"));
    }

}


function experiment_started(radio_version){
    // Global var
    experiment_running = true;

    // Enable buttons
    $("#send_cmd").removeAttr("disabled");
    $("#send_cmd").removeClass("disabled");
    $("#update_testbed").removeAttr("disabled");
    $("#update_testbed").removeClass("disabled");
    
    // Clear output filed in case something is here from before
    $("#output_field").val("");

    // Display which types of radios are in use
    $(".radio_type").text("Radio type: " + radio_version);
    $(".radio_type").css("visibility", "visible");
    $(".radio_type").css("color", "black");
}

function experiment_stopped(){
    // Clear global var
    available_devices = [];
    experiment_running = false;
    //TODO??? tx_msg_nbr = 0;

    // Disable buttons
    $("#send_cmd").prop("disabled", true);
    $("#send_cmd").addClass("disabled");
    $("#update_testbed").prop("disabled", true);
    $("#update_testbed").addClass("disabled");

    // User should still know what types of radio have been used
    $(".radio_type").css("color", "gray");
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

    // Init tooltips on tloris devices
    $(".node").tooltipster();

    // --------------------------------------------------------------------------------------------------------
    // Web Sockets and its handlers
    // --------------------------------------------------------------------------------------------------------

    // If websocket are on the same domain
    //var socket = io();

    // For different domain, WebSocket server (flask_server.py) must have CORS enabled 
    // https://socket.io/docs/v3/client-initialization/
    var socket = io({path: "/controller/socket.io"});

    // Page refreshed - check with broker
    console.log("Socket status", socket.connected)
    /*socket.emit("refresh");

    socket.on("after refresh", function(msg){
        
    });*/


    socket.on("after connect", function(msg){
        console.log("Successfully connected to server!");

        console.log(msg.data);

        // Check if experiment is already running
        if(msg.data !== "None"){
            console.log("Experiment is already running ["+ msg.data +"]");
            experiment_started(msg.data);

            // Update testbed tloris
            socket.emit("testbed update");
        }
    });

    socket.on("experiment started", function(msg){
        console.log("Experiment has just started!");

        experiment_started(msg.data);
        socket.emit("testbed update");
    });

    socket.on("experiment stopped", function(msg){
        console.log("Experiment has stopped");

        experiment_stopped();

        dropdown.remove_all();
        alert("Experiment stopped!")
    });

    socket.on("command response", function(msg){
        console.log("Received response [" + msg.count +"] from device: " + msg.device +" :" + msg.data);

        var formatted_msg = "[" + msg.count + "] " + msg.device + ":" + msg.data + "\n";

        // Append text into textarea (don't delete old one)
        $("#output_field").val( $("#output_field").val() + formatted_msg);
        // Scroll to bottom
        $("#output_field").scrollTop( $("#output_field")[0].scrollHeight);
    });

    socket.on("device state update", function(msg){
        
        // If this address appears for the first time
        var lgtc = msg.data;
        if (available_devices.indexOf(lgtc.address) < 0){
            console.log("Nev available device in testbed");
            available_devices.push(lgtc.address);
            dropdown.add_dev(lgtc.address);
        }

        // Update state of the device in the tloris
        tloris.update_dev(lgtc.address, lgtc.state);

    });

    socket.on("testbed state update", function(msg){
        console.log("Update whole testbed state.");

        // Reset all states
        tloris.remove_all();
        dropdown.remove_all();
        available_devices = [];

        // Cycle through received list and update
        for(let lgtc of msg.data){
            tloris.update_dev(lgtc.address, lgtc.state);
            dropdown.add_dev(lgtc.address);
            available_devices.push(lgtc.address);
        }
    });

    socket.on("info", function(msg){
        console.log("Received info");

        // Append text into textarea (don't delete old one)
        $("#output_field").val( $("#output_field").val() + msg.data);
        // Scroll to bottom
        $("#output_field").scrollTop( $("#output_field")[0].scrollHeight);
    });

    // --------------------------------------------------------------------------------------------------------
    // Buttons
    // --------------------------------------------------------------------------------------------------------

    // Send command (via submitting Enter or pressing button)
    $("#send_cmd").on("click", function(e){
        send_command();
    });

    $("#input_cmd").on("keyup", function(e){
        if(e.key === "Enter"){
            send_command();
        }
    });

    function send_command(){
        if (experiment_running == false){
            alert("No active experiment in the testbed");
            return false;
        }
        
        // Get the cmd and obtain its number
        var nbr;
        var cmd = $("#input_cmd").val();
        if (SYSTEM_COMMANDS.includes(cmd)){
            nbr = "-1";
        }
        else {
            tx_msg_nbr += 1;
            nbr = tx_msg_nbr.toString();
        }

        // Check which device is selected from dropdown menu
        var dev = "";
        if($("#select_device option:selected").val() == "None"){
            alert("Please select device!");
            return false;
        }
        else {
            dev = $("#select_device option:selected").text();
        }

        console.log("Send command [" + nbr + "] to device: " + dev );
        
        // Send it to server
        socket.emit("new command", {
            device: dev,
            count: nbr,
            data: cmd
        });
        return true;
    }


    // Button to clear output text
    $("#clear_output").on("click", function(event){
        console.log("Clear output");
        $("#output_field").val("");
    });

    // Button to update testbed state
    $("#update_testbed").on("click", function(event){
        console.log("Send request to update testbed state");
        if (experiment_running == false){
            alert("No active experiment in the testbed");
            return false;
        }
        socket.emit("testbed update");

        // TODO: display tooltip: "Up to date"
    });
});






