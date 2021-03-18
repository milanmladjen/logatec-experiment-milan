var tx_msg_nbr = 0;
var rx_msg_nbr = 0;

var experiment_started = 0;

var available_devices = [];

function dropdownAddDevice(dev){
    
    // Create new option (value = dd_LGTC66) because id LGTC66 is used elsewhere
    var newOption = document.createElement("option");
    newOption.text= dev;
    newOption.value = "dd_" + dev;
    
    // Add it to dropdown list
    var dropdown = document.getElementById("select_device");
    dropdown.options.add(newOption);
}

function dropdownDeleteDevice(dev){
    var dropdown = document.getElementById("select_device");

    // Test to see if it works :)
    for (var i=0; i<dropdown.length; i++){
        if(dropdown[i].childNodes[0].nodeValue === ("dd_" +dev)){
            dropdown.options[i] = null;
        }
    }

    // To delete all except first one (which is option "all") do:
    // dropdown.options.length = 1;
}

// Check if input command is in list of supported commands
function commandSupported(c){
    system_commands = [
        "SYNC_WITH_VESNA",
        "FLASH",
        "STATE",
        "EXIT",
        "START_APP",
        "STOP_APP",
        "RESTART_APP"
    ];

    app_commands = [
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


// Add device to the list of active devices
function statelistAddDevice(dev, state){
    
    // Create new <p> element
    var newP = document.createElement("p");
    newP.appendChild(document.createTextNode(dev + ":" + state));
    newP.setAttribute("id", dev);

    // Append it to the div
    var listdiv = document.getElementById("device_state_list");
    listdiv.appendChild(newP);
}

// Update device state in the list
function statelistUpdateDevice(dev, state){

    // Find the <p> element with the ID of device
    document.getElementById(dev).innerHTML = dev + ":" + state;
}

// Remove device from the list
function statelistDeleteDevice(dev){
    var element = document.getElementById(dev);
    element.remove();
}

// Delete whole list
function statelistRemove(){
    var listdiv = document.getElementById("device_state_list");

    while(listdiv.hasChildNodes()){
        listdiv.removeChild(listdiv.firstChild);
    }
}


// Websocket config (using jQuery on document ready)
$(document).ready(function(){

    // If websocket are on the same domain
    // var socket = io();

    // For different domain, WebSocket server (flask_server.py) must have CORS enabled 
    // https://socket.io/docs/v3/client-initialization/
    var socket = io("https://videk.ijs.si:80/", {path: "/controller/socket.io"});

    // You can also use different namespace, but then you must update the WS server as well
    // var socket = io("http://localhost:80/namespace_controller");


// Prepare html
    // Delete old output logs
    $("#output_field").val("");

// Handlers for events on client browser (using jQuery)

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
        dev_list = document.getElementById("select_device");
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


// Handlers for received messages from server

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
        statelistRemove();

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
            dropdownAddDevice(lgtc.address);
            statelistAddDevice(lgtc.address, lgtc.state);
        }
        // Else update device state in the device state list
        else{
            console.log("Update only one device state.");
            statelistUpdateDevice(lgtc.address, lgtc.state);
        }

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
                dropdownAddDevice(dev);
                statelistAddDevice(dev, elmnt.state);
            }
            // Else update device state in the device state list
            else{
                statelistUpdateDevice(dev, elmnt.state);
            }

            // TODO: Delete devices from the list if they are not in database
        }

        // TODO: make it a function and do:
        // msg.data.forEach(function);
        // This will call a "function" for each element in list
        
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


