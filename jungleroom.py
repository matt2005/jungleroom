#! /usr/bin/python
# the main script for the jungleroom project that runs on the raspberrypi
# inspirations drawn from the following sources:
# http://www.elinux.org/RPi_Low-level_peripherals
# http://www.acmesystems.it/i2c
# http://quick2wire.com/articles/i2c-and-spi/
# http://stackoverflow.com/questions/307305/play-a-sound-with-python
# retired : 
# http://www.raspberrypi-spy.co.uk/2012/08/reading-analogue-sensors-with-one-gpio-pin/#more-520
# http://www.doctormonk.com/2012/07/raspberry-pi-gpio-driving-servo.html

#                             +---+
#              3.3v power     |* *| 5v power
#          GPIO  0 (SDA)      |* *| 5v power
#          GPIO  1 (SCL)      |* *| Ground
# servo <- GPIO  4 (GPCLK0)   |* *| GPIO 14 (TXD)
#                  Ground     |* *| GPIO 15 (RXD)
#   PIR -> GPIO 17            |* *| GPIO 18 (PCM CLK) <- BTN1 (toggle)
#          GPIO 21 (PCM DOUT) |* *| Ground
#          GPIO 22            |* *| GPIO 23           <- BTN2 
#              3.3v power     |* *| GPIO 24           <- BTN3
#   Btn -> GPIO 10 (MOSI)     |* *| Ground
#          GPIO  9 (MISO)     |* *| GPIO 25  
#          GPIO 11 (SCLK)     |* *| GPIO  8 (CEO) 
#              Ground         |* *| GPIO  7 (CE1)
#                             +---+

import RPi.GPIO as GPIO, time, smbus, os, random
from AttinyStepper import AttinyStepper
from ServoPi import ServoPi

GPIO.setmode(GPIO.BCM)
# Set up the GPIO channels - one input and one output
GPIO.setup( 4, GPIO.OUT)  # Servo to open/close the door
GPIO.setup(17, GPIO.IN)   # PIR
GPIO.setup(18, GPIO.IN)   # BTN1 (toggle) open and close the door with a servo
GPIO.setup(23, GPIO.IN)   # BTN2 run the stepper motor
GPIO.setup(24, GPIO.IN)   # BTN3 play the sound of an animal

i2c = smbus.SMBus(1)

tinyStep  = AttinyStepper(0x10, 20)
doorServo = ServoPi(4, 0.002, 0.001, 0.02)

doorOpen = GPIO.input(18) == GPIO.HIGH

cableCarBottom = True

# Main program loop
while True:
	pirval   = GPIO.input(17) == GPIO.HIGH
	btn1val  = GPIO.input(18) == GPIO.HIGH
	btn2val  = GPIO.input(23) == GPIO.HIGH
	btn3val  = GPIO.input(24) == GPIO.HIGH
	lightval = 0

	if btn3val:
		files = os.listdir('./sounds')
		file = files[random.randint(0, len(files) - 1)]
		print 'btn 3 pressed. playing %s' % file
		os.system('aplay sounds/%s' % file)

	if btn2val:
		try:
			# let the stepper motor advance some steps
			if cableCarBottom:
				tinyStep.stepsForward(255)
				cableCarBottom = False
			else:
				tinyStep.stepsBackward(255)
				cableCarBottom = True
			time.sleep(5)
			
		except Exception as ex:
			print 'i2c error with the stepper: %s' % str(ex)

	if doorOpen != btn1val:
		servoInterval = servoOpenVal - servoCloseVal
		servoSteps = 80	
		if btn1val:
			print 'open the door'
			for i in range(1, servoSteps):
				doorServo.move(i / 80)
		else:
			print 'close the door'
			for i in range(1, servoSteps):
				doorServo.move(1 - (i / 80))
		doorOpen = btn1val			
	elif doorOpen:
		# send some impulses to keep the door open
		for i in range(10):
			GPIO.output(servoPin, False)
			time.sleep(servoOpenVal)
			GPIO.output(servoPin, True)
			time.sleep(servoRefreshPeriod)
			
	try:		 
		# get the light value analog reading from the attiny
		lightval = tinyStep.readAnalog8()
	except Exception as ex:
		print 'i2c error with the light sensor : %s' % str(ex)


	print "%i  %i  %i  %i  %i" % (btn1val, btn2val, btn3val, pirval, lightval)  

	time.sleep(0.05)

