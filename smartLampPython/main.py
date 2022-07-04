# smartLedFull
# Created at 2018-05-18 11:54:27.417216

#######################################
#       IMPORT AND CONSTANTS          #
#######################################

#Import
import streams
import i2c
from wireless import wifi
from espressif.esp32net import esp32wifi as wifi_driver
from zerynthapp import zerynthapp
from worldsemi.ws2812 import ledstrips as pixel

#
SENSOR_ADDRESS = 0x13

#App Info
UID ='BmwysJJ-QXaPyfZNAOtjZw'
TOKEN ='dyEfZqgJQIKR_wtKAB_WIA'

#WiFi Info
SSID = ''
PASSWORD = ''

#Strip Infos
num_leds = 60
strip_pin = D13
light_status = False
r = 0
g = 0
b = 80
brightness = 0.5

#Other infos
port = None
zapp = None
leds = None
darkness = 750

#0 = manual; 1 = automatic; 2 = colorCycle
mode = 0

#This flag is used to break the colorCycle loop.
#False: Go on; True: break.
breakFlag = False

######################################
#           FUNCTIONS                #
######################################

#This function initialize the device
def init():
    global port, leds
    streams.serial()
    pinMode(strip_pin, OUTPUT)
    
    #Led Strip
    leds = pixel.LedStrip(strip_pin, num_leds)
    leds.setall(r,g,b)
    stripOff()
    
    #Proximity and Ambient Light Sensor
    port = i2c.I2C(I2C1, SENSOR_ADDRESS)
    port.start()
    setting()
    
    #Wifi and ZerynthApp
    wifiInit()
    zerynthappInit()


#Set the configuration registers of the sensor 
def setting():
    #83h: --11 1111
    #Set the maximum value for IR LED current
    #for the higher sensibility
    port.write([0x83, 0x3F])


#Initialize the wifi connection
def wifiInit():
    try:
        wifi_driver.auto_init()
     
        print('Connecting...')
        wifi.link(SSID, wifi.WIFI_WPA2, PASSWORD)
        print('Connected to wifi')
    except Exception as e:
        print(e)


#Initialize the zerynthapp object
def zerynthappInit():
    global zapp
    try:
        
        print('Connecting to Zerynth App...')
        zapp = zerynthapp.ZerynthApp(UID, TOKEN)
        print('zapp object created!')
    
        #Attach the callback functions
        zapp.on('toggle', toggle_strip)
        zapp.on('query', query_status)
        zapp.on('mode', mode_change)
        zapp.on('send_info', set_info)
    
    
        print('Start the app instance...')
        zapp.run()
        print('Instance started.')
    
    except Exception as e:
        print(e)


#Read the proximity from the device
def readProx():
    #80h: 0000 1000
    #Set on the prox. od bit
    port.write([0x80, 0x08])
    
    #Read the Proximity Measurement Result Registers
    #Join the 2bytes in the right order
    #Print the result on console
    data=port.write_read(0x87,2)
    prox_value = build_value(data[1], data[0])
    print('prox value = ', prox_value)
    return prox_value


#Read the ambient light from the device
def readLight():
    #80h: 0001 0000
    #Set on the als. od bit
    port.write([0x80, 0x10])
    
    #Read the Ambient Light Result Registers
    #Join the 2bytes in the right order
    #Print the result on console
    data=port.write_read(0x85,2)
    light_value = build_value(data[1], data[0])
    print('lux value = ', light_value)
    return light_value


def build_value(lo,hi):
    return (lo | (hi<<8))


#Callback function invoked to send the strip leds current infos
#such as light status, rgb color, mode, brightness and light tolerance.
def query_status(*args):
    print('Query status, returning:', light_status)
    hexcolor = '#'
    hexcolor += hex(r)[2:] + hex(g)[2:] + hex(b)[2:]
    
    print("Infos sended.")
    return {'ls': light_status,
        'color': hexcolor,
        'mode': mode,
        'brightness': brightness,
        'darkness': darkness}


#Callback function invoked to change the current operating mode.
def mode_change(new_mode):
    global mode, breakFlag
    
    #Set breakFlag to False to allow the
    #color cycle to perform it's loop
    if breakFlag is True:
        breakFlag = False
    
    #Set breakFlag to True if changing to
    #a new mode, different from color cycle,
    #in order to break the color cycle loop
    #and invoke the stripOn if light status
    #is True (It'll update the leds with rgb
    #infos stored in global r,g,b)
    if new_mode != 2:
        breakFlag = True
        if light_status is True:
            stripOn()
    
    #Update the mode
    mode = new_mode
    print("New mode:", mode)


#Callback function triggered after an user pressed the "CHANGE" button.
#Stores all the infos in global variables and update the leds behaviour.
def set_info(colore_strip, bright, dark):
    global light_status, r, g, b, brightness, darkness
    
    r = int ((colore_strip[1] + colore_strip[2]), 16)
    g = int ((colore_strip[3] + colore_strip[4]), 16)
    b = int ((colore_strip[5] + colore_strip[6]), 16)
    brightness = (float(bright)/10)
    darkness = 150 * int(dark)
    
    print("Setting these values: ",r+g+b)
    print("setting brightness: ", brightness)
    print("setting darkness:", darkness)
    
    #Update the leds behaviour.
    if light_status is True and mode != 2:
        stripOn()


#This function will light the leds in a color cycle. 
#All the rgb infos in the function are stored in local variables,
#in order to save the status of the color picker (stored in r,g,b global variables)
#and to light the strip led properly if a mode change occour.
def colorCycle():
    print("New cycle!")
    rgbColour=[255, 0, 0]
    decColour = 0
    incColour = 0
    i=0
    
    for decColour in range (0, 3):
        if(decColour is 2):
            incColour = 0
        else:
            incColour += 1
        
        for i in range (0, 255):
            if breakFlag is True:
                return
                
            else:
                rgbColour[decColour] = rgbColour[decColour] - 1
                rgbColour[incColour] += 1
            
                leds.setall(rgbColour[0], rgbColour[1], rgbColour[2])
                
                if light_status is True:
                    leds.brightness(brightness)
                    leds.on()
            
                i += 1
                sleep(10)
            
        
        decColour += 1


#Callback function triggered after an user pressed
#the lightbulb icon on the app to switch the light.
def toggle_strip(*args):
    print("Toggling light")
    global light_status, zapp
    
    light_status = not light_status
    
    if light_status is True:
        stripOn()
    else:
        stripOff()
    
    #Send the new light ststus to the app
    print('Send new light_status: ', light_status)
    zapp.event({'light_status': light_status})
    print('Status sent.')


#Turns on the light using r,g,b colors
#and brightness for intensity of light
def stripOn():
    print("setting it on")
    leds.setall(r,g,b)
    leds.brightness(brightness)
    leds.on()


def stripOff():
    print("setting it off")
    leds.brightness(0.0)
    leds.on()


#############################################
#                MAIN                       #
#############################################

init()

while True:
    #Automatic mode
    if mode == 1:
        #read proximity value
        prox_value = readProx()
        #read light intensity 
        light_value = readLight()
    
        #If it's dark enough and an object is near...
        if(light_value <= darkness and prox_value >= 2070):
            #...turn on the leds if they're off.
            if(light_status is False):
                light_status = True
                stripOn()
                zapp.event({'light_status': light_status})
                
        elif(light_status is True):
            #Turn them off otherwise.
            light_status = False
            stripOff()
            zapp.event({'light_status': light_status})
    
    #Color Cycle mode
    elif mode == 2:
        colorCycle()
    
    sleep(200)
