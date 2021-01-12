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


// Websocket config 
$(document).ready(function(){

    // sending a connect request to the server.
    // var socket = io(); // If you use different url than http server, put it in the brackets
    // io.connect();
    //var socket = io.connect('http://localhost:5000');
    var socket = io();

// Handlers for events on client browser (using jQuery)

    $("#send_cmd").on("click", function(event){
        tx_msg_nbr += 1;
        var nbr = tx_msg_nbr.toString();

        console.log("Send new command [" + nbr + "]");
        socket.emit("new command", {
            device: "LGTC66",
            count: nbr,
            data: $("#input_cmd").val()
        });
        return false;
        // TODO: add filtering for incorrect commands
    });


// Handlers for received messages from server

    socket.on("after connect", function(msg){
        console.log("Successfully connected to server!", msg.data);
    });

    socket.on("command response", function(msg){
        console.log("Received response [" + msg.count +"] from device: " + msg.device +" :" + msg.data);



    });

    socket.on("update devices", function(msg){
        console.log("Update device list");

    });

});