from sense_hat import SenseHat
import time
import mqtt_link as mqttnd
import json
sense = SenseHat()

OFFSET_LEFT = 1
OFFSET_TOP = 2

NUMS =[1,1,1,1,0,1,1,0,1,1,0,1,1,1,1,  # 0
       0,1,0,0,1,0,0,1,0,0,1,0,0,1,0,  # 1
       1,1,1,0,0,1,0,1,0,1,0,0,1,1,1,  # 2
       1,1,1,0,0,1,1,1,1,0,0,1,1,1,1,  # 3
       1,0,0,1,0,1,1,1,1,0,0,1,0,0,1,  # 4
       1,1,1,1,0,0,1,1,1,0,0,1,1,1,1,  # 5
       1,1,1,1,0,0,1,1,1,1,0,1,1,1,1,  # 6
       1,1,1,0,0,1,0,1,0,1,0,0,1,0,0,  # 7
       1,1,1,1,0,1,1,1,1,1,0,1,1,1,1,  # 8
       1,1,1,1,0,1,1,1,1,0,0,1,0,0,1]  # 9

# Displays a single digit (0-9)
def show_digit(val, xd, yd, r, g, b):
    offset = val * 15
    for p in range(offset, offset + 15):
        xt = p % 3
        yt = (p-offset) // 3
        sense.set_pixel(xt+xd, yt+yd, r*NUMS[p], g*NUMS[p], b*NUMS[p])

# Displays a two-digits positive number (0-99)
def show_number(val, r, g, b):
    abs_val = abs(val)
    tens = abs_val // 10
    units = abs_val % 10
    if (abs_val > 9): show_digit(tens, OFFSET_LEFT, OFFSET_TOP, r, g, b)
    show_digit(units, OFFSET_LEFT+4, OFFSET_TOP, r, g, b)


################################################################################
# MAIN

sense.clear()
#Set intial variables before loop
target_temp=75 # we want it to be 75 degrees celsius
unit = 'celsius'
temp = round(sense.get_temperature())
cooling = False # understanding whether it is heating or cooling
heating = True
previousTemp = 10000000000000000
previousHumidity = 10000000000000000
theClient = mqttnd.connect_mqtt()

while True:
    #set running light to on and green
    sense.set_pixel(7, 0, (0, 255, 0))
    events = sense.stick.get_events()

# heating and cooling intensitys and displays
    if temp<target_temp:  # intensity heating
        heating = True
        cooling = False
        if abs(temp-target_temp)>abs(5):
            sense.set_pixel(0, 0, (255, 0, 0))
            sense.set_pixel(1, 0, (0, 0, 0))
            sense.set_pixel(3, 0, (255, 255, 0))
            show_number(temp, 200, 0, 60)
        elif abs(temp-target_temp)<abs(5):    
            sense.set_pixel(0, 0, (100, 0, 0))
            sense.set_pixel(1, 0, (0, 0, 0))
            sense.set_pixel(3, 0, (125, 125, 0))
            show_number(temp, 200, 0, 60)
    elif temp > target_temp:  # intensity cooling
        cooling = True
        heating = False
        if abs(temp-target_temp)>abs(5):
            sense.set_pixel(3, 0, (255, 255, 0))
            sense.set_pixel(1, 0, (0, 0, 255))
            sense.set_pixel(0, 0, (0, 0, 0))
            show_number(temp, 200, 0, 60)
        elif abs(temp-target_temp)<abs(5):
            sense.set_pixel(3, 0, (125, 125, 0))
            sense.set_pixel(1, 0, (0, 0, 100))
            sense.set_pixel(0, 0, (0, 0, 0))
            show_number(temp, 200, 0, 60)
    ######################################################
    # updates temperature
    if unit =='farenheit':  # needs this in case it is set to farenheit
        if ((sense.get_temperature() * 9/5) + 32) > 99:
            temp = 99
        else:
            temp = round(((sense.get_temperature() * 9/5) + 32),0)
            temp = int(temp)
    else:
      temp = round(sense.get_temperature())
    #############################################
    # button pushes
    for event in events:
      # Skip releases
        if event.action == "pressed" and event.direction == "up":
            target_temp=target_temp+1
            show_number(target_temp, 200, 0, 60)
            time.sleep(.85)
        if event.action == "pressed" and event.direction == "down":
            target_temp=target_temp-1
            show_number(target_temp, 200, 0, 60)
            time.sleep(.85)
        if event.action == "pressed" and event.direction == "left" and unit == 'farenheit': #converts to C
            unit = 'celsius'
            temp = sense.get_temperature() # conversion for actual temp
            temp = int(temp)
        if event.action == "pressed" and event.direction == "right" and unit == 'celsius': #converts to F
            unit = 'farenheit'
            if ((temp * 9/5) + 32) > 99: # conversion for actual temp
                temp = 99
            else:
                temp = round(((temp * 9/5) + 32),0)
                temp = int(temp)
        elif event.action == "pressed" and event.direction == "middle": #displays cuurent target tempat
            show_number(target_temp,200,0,60)
            
    ######################################
    # mqtt messages
    
    humidity = int(sense.get_humidity())
    
    # checks for changes
    if previousTemp != temp or previousHumidity != humidity:
        previousTemp = temp
        previousHumidity = humidity
        secondJSON = {"Temperature": temp, "Unit": unit,"Humidity": humidity,"Heating": heating,"Cooling": cooling}
        theString = json.dumps(secondJSON)

        mqttnd.send_mqtt(theClient, "cse34468-su24/MaxGroup/lab-04/info/", theString)
