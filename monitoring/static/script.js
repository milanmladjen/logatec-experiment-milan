var tx_msg_nbr = 0;
var rx_msg_nbr = 0;

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
    possible_commands = [
        "START_APP",
        "RESET_APP",
        "STOP_APP",
        "STATE",
        "LINES"
    ];

    if(possible_commands.includes(c)){
        return true;
    }
    else{
        return false;
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



// Websocket config (using jQuery on document ready)
$(document).ready(function(){

    // sending a connect request to the server.
    // var socket = io(); // If you use different url than http server, put it in the brackets
    // io.connect();
    //var socket = io.connect('http://localhost:5000');
    var socket = io();

// Handlers for events on client browser (using jQuery)

    $("#send_cmd").on("click", function(event){

        // Get message number
        tx_msg_nbr += 1;
        var nbr = tx_msg_nbr.toString();

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

        // Check if command is supported
        cmd = $("#input_cmd").val();
        if(!commandSupported(cmd)){
            alert("Command not supported!")
            return false;
        }

        // If command is STATE command, give it number 0, so broker will know
        if(cmd == "STATE"){
            nbr = "0";
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
        console.log("Successfully connected to server!", msg.data);
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
        var dev = msg.device;
        if (available_devices.indexOf(dev) < 0){
            console.log("Nev available device in testbed");
            available_devices.push(dev);
            dropdownAddDevice(dev);
            statelistAddDevice(dev, msg.data);
        }
        // Else update device state in the device state list
        else{
            console.log("Update only one device state.");
            statelistUpdateDevice(dev, msg.data);
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
        console.log("Send request to update testbed state");
        socket.emit("testbed update");
    });

});


