/* flag = 0: manual mode
*  flag = 1: automatic mode
*  flag = 2: color cycle activated */
var flag = 0


/* All the (something)Mode functions trigger the mode_change callback on device. */

//This function asks the device to set the manual mode.
function manualMode(){
	    flag = 0;
		$('#automaticMode').attr("src", "automatica.png");
		$('#colorCycleMode').attr("src", "cerchio.png");
		$('#manualMode').attr("src", "manuale_r.png");
	    Z.call('mode', [0]);
	}
	
//This function asks the device to set the automatic mode.	
function automaticMode(){
	    flag = 1;
		$('#manualMode').attr("src", "manuale.png");
		$('#colorCycleMode').attr("src", "cerchio.png");
		$('#automaticMode').attr("src", "automatica_r.png");
	    Z.call('mode', [1]);

}

//This function asks the device to set the color cycle mode.
function colorCycleMode(){
	flag = 2;
	$('#manualMode').attr("src", "manuale.png");
	$('#automaticMode').attr("src", "automatica.png");
	$('#colorCycleMode').attr("src", "cerchio_r.png");
	Z.call('mode', [2]);
}

//This function shows the User Guide Dialog.
function helpMode(){
	$('#dialog').dialog("open");
}

/* This function receive the light_status from device and
   invokes the change_lightbulb function */
function event_callback(event){
    var light_status = event.payload.light_status;
	change_lightbulb(light_status);
}

//This fuction updates the lightbulb icon.
function change_lightbulb(light_status){
	var val = light_status? "on.png" : "off.png";
	$('#lightbulb').attr("src", val);
}
	
/* This function will be invoked clicking on the lightbulb icon
   and will trigger the toggle_strip callback on device. */
function toggle_callback(){
	if(flag != 1)
	    Z.call('toggle', [42]);
}

/* This function will be invoked everytime the app starts
   and will trigger the query_status callback on device.*/
function online_callback(){
    Z.call('query', [42], query_callback);
}

/* This function updates all the infos about rgb color,
   mode, brightness and light tolerance. */
function query_callback(msg){
	//Updating the light status
	change_lightbulb(msg.res.ls);
	
	//Updating the rgb parameters
	$('#color').val(msg.res.color);
	$(document).ready(function() {
        $('#demo').hide();
        $('#picker').farbtastic('#color');
    });
	
	//Updating the mode buttons
	flag = msg.res.mode;
	if (flag == 1)
		automaticMode();
	else if (flag == 2)
		colorCycleMode();
	
	//Updating the brightness bar
	bright = msg.res.brightness * 10;
	$('#brightBar').val(bright);
	
	//Updating the darkness bar
	dark = msg.res.darkness / 150;
	$('#toleranceBar').val(dark);
	changeSun();
}

/* This function sends all the infos about rgb color,
   brightness and light tolerance. 
   It will trigger the set_info callback on device. */
function sendinfo(){
	var colore = $('#color').val();
	var brightness = $('#brightBar').val();
	var darkness = $('#toleranceBar').val();
	Z.call('send_info', [String(colore), brightness, darkness]);
}

function changeSun(){
	    
	value=document.getElementById("toleranceBar").value;
		
	if(value<=3){
		document.getElementById("sun").src="moon.png";
	}
	else if(value>3 && value<=5){
		document.getElementById("sun").src="sun_1.png";
	}
	else if(value>5 && value<8){
		document.getElementById("sun").src="sun_2.png";
	}
	else if(value>=8 && value<=10){
		document.getElementById("sun").src="sun_3.png";
	}
		
}
	
/* This function attachs the callback functions and
   create the dialog object. */
function init(){
	Z.init({
		on_event: event_callback,
		on_connected: online_callback,
	});
	
	$('#dialog').dialog({
		autoOpen: false,
		height: 450,
		width: 275,
		resizable: false,
		dialogClass: 'no-close success-dialog'
	});
}
