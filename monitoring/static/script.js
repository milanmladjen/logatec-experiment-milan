var tx_msg_nbr = 0;
var rx_msg_nbr = 0;

function dropdownAddDevice(dev){
    var dropdown = document.getElementById("select_device");
    var newOption = document.createElement("option");

    newOption.text= dev;
    newOption.value = dev;
    dropdown.options.add(newOption);
}

function dropdownDeleteDevice(dev){
    var dropdown = document.getElementById("select_device");

    // Test to see if it works :)
    for (var i=0; i<dropdown.length; i++){
        if(dropdown[i].childNodes[0].nodeValue === dev){
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
        "STATE"
    ];

    if(possible_commands.includes(c)){
        return true;
    }
    else{
        return false;
    }
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

        // Check which device is selected
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

    socket.on("update devices", function(msg){
        console.log("Update device list");

    });


    // Button to clear output text
    $("#clear_output").on("click", function(event){
        console.log("Clear output");
        $("#output_field").val("");
    });

});