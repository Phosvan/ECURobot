########CREATED FOR 2019 ECU ATMAE ROBOTICS COMPETITION##########

#######################################################################
# Import all required libraries
#
import pygame
import serial
import time
import socket
import os
from gpiozero import LED
from gpiozero import PWMLED
#
#
#######################################################################

#######################################################################
# Set this script to run with a higher priority. Requires SU privileges
#
os.nice(-15)
#
#
#######################################################################

#######################################################################
# Begin TCP socket initialization. Enter IP/Port information of server here
# 
srv_address = ('172.16.0.99', 32768)

# Define a subroutine that can be called to receive data from the socket
def receive_data():
	data = sock.recv(128)

	return data.decode('utf-8')
#
#
#######################################################################

#######################################################################
# Configure mappings for GPIO
# 1
elevatorStepperStep = LED(23)
elevatorStepperDir = LED(24)
sideshiftStepperStep = LED(25)
sideshiftStepperDir = LED(8)
gripStepperStep = LED(7)
gripStepperDir = LED(1)

leftPWM = PWMLED(12)
rightPWM = PWMLED(13)
leftDriveDirection = LED(17)
rightDriveDirection = LED(27)

#
#
#######################################################################

#######################################################################
# Set up textprint for the user display
#
# Color declarations go here
BLACK = pygame.Color('black')
WHITE = pygame.Color('white')

# This class sets up text printing
class TextPrint(object):
	def __init__(self):
		self.reset()
		self.font = pygame.font.Font(None, 20)

	def tprint(self, screen, textString):
		textBitmap = self.font.render(textString, True, BLACK)
		screen.blit(textBitmap, (self.x, self.y))
		self.y += self.line_height

	def reset(self):
		self.x = 10
		self.y = 10
		self.line_height = 15

	def indent(self):
		self.x += 10

	def unindent(self):
		self.x -= 10

# Classes are configured, go ahead and initialize pygame
pygame.init()

# Set the width and height of the screen window (width, height), set window name
screen = pygame.display.set_mode((500, 700))
pygame.display.set_caption("ECU ATMAE - BotPi TCP Client")

# Loop until the user clicks the close button.
done = False

# Used to manage how fast the screen updates.
clock = pygame.time.Clock()

# Get ready to print.
textPrint = TextPrint()
#
#
#######################################################################

#######################################################################
# Configure global variables for use by the main loop
#

# Declare two variables for use as a debounce and time tracker for serial/controller interfaces
# NOTE: MIGHT CAN BE DEPRECATED AFTER TESTING!!! #
timerThreshold = 0
debounceThreshold = 0
autoThreshold = 0

# Global variables for drive/stepper control
ltDrive = 0
rtDrive = 0
ltDriveStatus = 0
rtDriveStatus = 0
driveMode = 0
elevatorStepper = 0
gripStepper = 0
sideshiftStepper = 0
packet = ""
serBlockData = ""
serNoBlockData = ""
bytepacket = ""

# Global variables for sensor control. Initialized at non-default state of 0/1 for debug purposes
elevatorLimit0Status = 2
elevatorLimit1Status = 2
elevatorLimit2Status = 2
gripLimitStatus = 2
sideshiftLimitStatus = 2

# Global variables for logic functions go here
firstRun = False
elevatorAutoIntent = False
elevatorUpIntent = False
elevatorDownIntent = False
autoForwardIntent = False
autoForward = False
autoForwardReady = False
#
#
#######################################################################

#######################################################################
# Subroutines referenced in the main loop go here
#

def serBlockRead():
	global serBlockData
	if (serBlock.in_waiting > 0):
		serBlockData = (serBlock.readline())

def serNoBlockRead():
	global serNoBlockData
	global elevatorLimit0Status
	global elevatorLimit1Status
	global elevatorLimit2Status
	global gripLimitStatus
	global sideshiftLimitStatus
	global ltDriveStatus
	global rtDriveStatus
	if  (serNoBlock.in_waiting > 0):
		serNoBlockData = serNoBlock.readline()
		if  (serNoBlockData != ""):
			serNoBlockData =  (serNoBlockData.decode("UTF-8"))
			sensorDataParsed = serNoBlockData.split(',')
			elevatorLimit0Status = int(sensorDataParsed [0])
			elevatorLimit1Status = int(sensorDataParsed [1])
			elevatorLimit2Status = int(sensorDataParsed [2])
			gripLimitStatus = int(sensorDataParsed [3])
			sideshiftLimitStatus = int(sensorDataParsed [4])
			ltDriveStatus = int(sensorDataParsed [5])
			rtDriveStatus = int(sensorDataParsed [6])

def createBlockPacket():
	global blockPacket
	global byteBlockPacket
	blockPacket = ("<%s,%s,%s,%s,%s,%s>")%(
		hex(driveMode),
		hex(ltDrive),
		hex(rtDrive),
		hex(elevatorStepper),
		hex(gripStepper),
		hex(sideshiftStepper)
		)
	byteBlockPacket = bytes(blockPacket, 'utf-8')

def createNoBlockPacket():
	global noBlockPacket
	global byteNoBlockPacket
	noBlockPacket = ("<%s,%s,%s>")%(
		hex(driveMode),
		hex(ltDrive),
		hex(rtDrive)
		)
	byteNoBlockPacket = bytes(noBlockPacket, 'utf-8')

def updateBlockControl():
	global byteBlockPacket
	if (time.time() > timerThreshold):
		serBlock.write(byteBlockPacket)

def updateNoBlockControl():
	global byteNoBlockPacket
	global timerThreshold
	if (time.time() > timerThreshold):
		serNoBlock.write(byteNoBlockPacket)
		#timerThreshold = time.time() + 0.1

#
#
#######################################################################

# -------- Main Program Loop -----------
# initialize the serial lines and then drop into the main program loop
#
# NOTE: If something isn't working, make sure the correct serial line is selected
#       by opening a Terminal window and typing 'ls /dev/serial/by-id/' to get the correct
#       device numbers. Place those in the serial lines below.
# Enter main loop
while not done:

	#######################################################################
	# Set up TCP socket. This must be called every loop to ensure we only
	# update upon receiving a new input from our controller. This ensures
	# this script is dictated solely by the speed of our network.
	#
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(srv_address)
	#
	#
	#######################################################################

	#######################################################################
	# Get the network packet
	#
	udp_controls = str(receive_data())
	""" NOTE: MAY BE USEFUL FOR TESTING
	if (udp_controls == 'QUIT'):
		break
	"""
	# Parse the packet...
	prs_controls = list(udp_controls)
	prs_controls.pop(0)
	prs_controls.pop(len(prs_controls)-1)
	prs_controls = ''.join(prs_controls)
	prs_controls = prs_controls.split(',')
	# End parsing

	# Convert parsed packet into useable values
	p_axes    = [
		float(prs_controls[0]),
		float(prs_controls[1]),
		float(prs_controls[2]),
		float(prs_controls[3])
	]

	p_buttons = [
		int(prs_controls[4]),
		int(prs_controls[5]),
		int(prs_controls[6]),
		int(prs_controls[7]),
		int(prs_controls[8]),
		int(prs_controls[9]),
		int(prs_controls[10]),
		int(prs_controls[11]),
		int(prs_controls[12]),
		int(prs_controls[13]),
		int(prs_controls[14]),
		float(prs_controls[15]),
		float(prs_controls[16])
	]
	#
	#
	#######################################################################

	#######################################################################
	# EVENT PROCESSING STEP
	#
	# Possible joystick actions: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
	# JOYBUTTONUP, JOYHATMOTION
	for event in pygame.event.get(): # User did something.
		if event.type == pygame.QUIT: # If user clicked close.
			done = True # Flag that we are done so we exit this loop.

	#######################################################################
	# Drive control logic
	#

	if p_axes[1] < 0: # If y axis < 0, move forward
		textPrint.tprint(screen, ("y<0, move forward"))
		driveMode = 1 #See motorArduino code for ref
		if p_axes[2] == 0: # If x-axis is 0, no turn. Motor = yDrive
			textPrint.tprint(screen, ("x=0"))
			ltDrive = int(150*( ( -p_axes[1] )))
			rtDrive = int(150*( ( -p_axes[1] )))

			leftPWM.value = -p_axes[1]
			rightPWM.value = -p_axes[1]
			leftDriveDirection.off()
			rightDriveDirection.off()

		elif p_axes[2] > 0: # If x-axis is > 0, right turn.
			textPrint.tprint(screen, ("x>0"))
			ltDrive = int(150*( ( -p_axes[1] )))
			rtDriveLogic = ( ( -p_axes[1] ) - (-p_axes[1])*(p_axes[2]))
			rtDrive = int(150*(rtDriveLogic))

			leftPWM.value(-p_axes[1])
			rightPWM.value(rtDriveLogic)
			leftDriveDirection.off()
			rightDriveDirection.on()
		elif p_axes[2] < 0: # If x-axis is < 0, left turn.
			textPrint.tprint(screen, ("x>0"))
			ltDriveLogic = ( (-p_axes[1]) - (-p_axes[1])*(-p_axes[2]))
			ltDrive = int(150*(ltDriveLogic))
			rtDrive = int(150*( (-p_axes[1] )))

			leftPWM.value(ltDriveLogic)
			rightPWM.value(-p_axes[1])
			leftDriveDirection.on()
			rightDriveDirection.off()

	if p_axes[1] > 0: # If y axis > 0, move backward
		textPrint.tprint(screen, "y>0, move backward")
		driveMode = 2 #See motoroArduino code for ref
		if p_axes[2] == 0:
			textPrint.tprint(screen, ("x=0"))
			ltDrive = int(150*( (p_axes[1] )))
			rtDrive = int(150*( (p_axes[1] )))
		elif p_axes[2] > 0: # If x-axis is > 0, right turn.
			textPrint.tprint(screen, ("x>0"))
			ltDriveLogic = ( (p_axes[1]) - (p_axes[1])*(p_axes[2]))
			ltDrive = int(150*(ltDriveLogic))
			rtDrive = int(150*( (p_axes[1] )))
		elif p_axes[2] < 0: # If x-axis is < 0, left turn.
			textPrint.tprint(screen, ("x>0"))
			ltDrive = int(150*( (p_axes[1] )))
			rtDriveLogic = ( (p_axes[1]) - (p_axes[1])*(-p_axes[2]))
			rtDrive = int(150*(rtDriveLogic))

	if p_axes[1] == 0: # If y-axis is 0, we're not moving. Zero all data
		driveMode = 0
		ltDrive = 0
		rtDrive = 0
		if round(p_axes[2], 3) == 1:
			driveMode = 4
		elif round(p_axes[2], 3) == -1:
			driveMode = 3
	#
	#
	#######################################################################

	#######################################################################
	# Stepper control logic
	#

	#This section maps dPad Up and Down to elevatorStepper Up/Down
	if (p_buttons[12] == 0):
		elevatorStepper = 0
		elevatorStepperStep.off()
	elif (p_buttons[12] == -1):
		elevatorStepper = 1
		elevatorStepperDir.on()
		elevatorStepperStep.on()
	elif (p_buttons[12] == 1):
		elevatorStepper = 2
		elevatorStepperDir.off()
		elevatorStepperStep.on()

	#This section maps dPad Left/Right to sideshiftStepper Left/Right
	if (p_buttons[11] == 0):
		sideshiftStepper = 0
	elif (p_buttons[11] == -1):
		sideshiftStepper = 3
	elif (p_buttons[11] == 1):
		sideshiftStepper = 4
	
	#This section maps bumpers to gripStepper control	
	if (p_buttons[4] == 1):
		gripStepper = 1
		gripStepperDir.on()
		gripStepperStep.on()
	if (p_buttons[5] == 1):
		gripStepper = 2
		gripStepperDir.off()
		gripStepperStep.on()
	#If both bumpers are not depressed or both bumpers are depressed, do nothing.
	if ((p_buttons[4] == 0 and p_buttons[5] == 0) or (p_buttons[4] == 1 and p_buttons[5] == 1)):
		gripStepper = 0
		gripStepperStep.off()
		gripStepperDir.off()
	
	#
	# This section of code configures auto up/down
	# NOTE: because code loops are not run between TCP packet receives,
	# the code blocks on the final leg of the up/down movement, which means
	# NO OVERRIDE!!!!!
	# EX: if at full bottom, non-blocking until limitswitch 2 is activated.
	#     once it is activated, drive motors are to stop and ignore user input
	#     until limitswitch 3 is activated. If neither happen within the timeout
	#     period, stop all motion and resume user input.
	#
	# For the logic to work properly, this section of code must be placed after
	# the manual control code as this should always override
	#
	if (p_buttons[2] == 1 and elevatorAutoIntent == False): 			# If Y button is pressed and we're not already intending to auto elevate
		elevatorAutoIntent = True# 										# Set our intention to auto elevate to TRUE
		elevatorUpIntent = True
		
	if (p_buttons[1] == 1 and elevatorAutoIntent == False):
		elevatorAutoIntent = True
		elevatorDownIntent = True
		
	if ((elevatorAutoIntent == True) and (elevatorUpIntent == True)):
		elevatorStepper = 2
		if ((elevatorLimit2Status == 0) or (p_buttons[3])):
			elevatorStepper = 0
			elevatorAutoIntent = False
			elevatorUpIntent = False
		
	if ((elevatorAutoIntent == True) and (elevatorDownIntent == True)):
		elevatorStepper = 1
		if ((elevatorLimit0Status == 0) or (p_buttons[3])):
			elevatorStepper = 0
			elevatorAutoIntent = False
			elevatorDownIntent = False
	#
	#
	#######################################################################
	
	#######################################################################
	# We need to 'home' our stepper motors so we know where they are.
	# This is a BLOCKING subroutine that will send elevator to its lowest position
	# and move sideshift to the far left position.
	# This code can be commented out safely, or set firstRun to False and this won't run.
	while (firstRun == True):
		while (elevatorLimit0Status != 0):
			createNoBlockPacket()
			updateNoBlockControl()
			serNoBlockRead()
			if (elevatorLimit0Status != 0):
				elevatorStepper = 1
			else:
				elevatorStepper = 0
			"""if (sideshiftLimitStatus != 0):
				sideshiftStepper = 1
			else:
				sideshiftStepper = 0"""
			createBlockPacket()
			time.sleep(0.01)
			updateBlockControl()
			time.sleep(0.01)
			serBlockRead()
			print(elevatorLimit0Status)
			if (elevatorLimit0Status == 0):
				firstRun = False
				autoForwardIntent = True
	if (autoForwardIntent == True):
		if p_buttons[7] == 1:
			autoThreshold = time.time() + 4
			autoForward = True
	elif (autoForward == True and p_buttons[7] == 1):
			autoForward = False
	if (autoForward == True and (time.time() < autoThreshold)):
			driveMode = 1
			ltDrive = 80
			rtDrive = 75
			print("True!")
	if (autoForward == True and (time.time() > autoThreshold)):
			autoForward = False
			autoForwardIntent = False

	#######################################################################
	# Condense information into a packet for TX over serBlock and serNoBlock
	#
	#createBlockPacket()
	#createNoBlockPacket()

	# SEND OUT OVER SERIAL LINK
	# if time has exceeded the threshold.
	#updateBlockControl()
	#updateNoBlockControl()
		
	#######################################################################
	# Read the serial lines and load those values into a string
	# 
	#serBlockRead()
	#serNoBlockRead()
	
	
	#######################################################################
	# DRAWING STEP
	#
	# First, clear the screen to white. Don't put other drawing commands
	# above this, or they will be erased with this command.
	screen.fill(WHITE)
	textPrint.reset()

	textPrint.tprint(screen, 'Receiving Controls...')

	# Begin main body...
	textPrint.indent()

	# Thumbsticks...
	textPrint.tprint(screen, ("Left Thumbstick (x, y): %.3f, %.3f")%(p_axes[0], p_axes[1]))
	textPrint.tprint(screen, ("Right Thumbstick (x, y): %.3f, %.3f")%(p_axes[2], p_axes[3]))
	textPrint.tprint(screen, '')

	# Buttons...
	textPrint.tprint(screen, ("A Button: %i")%( p_buttons[0] ))
	textPrint.tprint(screen, ("B Button: %i")%( p_buttons[1] ))
	textPrint.tprint(screen, ("X Button: %i")%( p_buttons[2] ))
	textPrint.tprint(screen, ("Y Button: %i")%( p_buttons[3] ))
	textPrint.tprint(screen, ("Left Bumper: %i")%( p_buttons[4] ))
	textPrint.tprint(screen, ("Right Bumper: %i")%( p_buttons[5] ))
	textPrint.tprint(screen, ("Start Button: %i")%( p_buttons[7] ))
	textPrint.tprint(screen, ("Back Button: %i")%( p_buttons[6] ))
	textPrint.tprint(screen, ("Guide Button: %i")%( p_buttons[8] ))
	textPrint.tprint(screen, ("Left Stick Click: %i")%( p_buttons[9] ))
	textPrint.tprint(screen, ("Right Stick Click: %i")%( p_buttons[10] ))
	textPrint.tprint(screen, ("DPAD: %1.f")%( p_buttons[12]))

	# Drive Control Information
	textPrint.tprint(screen, ("driveMode: %i")%driveMode)
	textPrint.tprint(screen, ("ltMotor: %i")%ltDrive)
	textPrint.tprint(screen, ("rtMotor: %i")%rtDrive)

	# Control Logic
	textPrint.tprint(screen, ("timeTime: %3.f")%time.time())
	textPrint.tprint(screen, ("debounceThreshold: %3.f")%debounceThreshold)

	# Sensor Status
	textPrint.tprint(screen, ("elevatorLimit0Status: %i")%elevatorLimit0Status)
	textPrint.tprint(screen, ("elevatorLimit1Status: %i")%elevatorLimit1Status)
	textPrint.tprint(screen, ("elevatorLimit2Status: %i")%elevatorLimit2Status)
	textPrint.tprint(screen, ("gripLimitStatus: %i")%gripLimitStatus)
	textPrint.tprint(screen, ("sideshiftLimit0Status: %i")%sideshiftLimitStatus)

	textPrint.tprint(screen, ("serBlockData: %s")%serBlockData)
	textPrint.tprint(screen, ("serNoBlockData: %s")%serNoBlockData)
	textPrint.tprint(screen, ("AutoIntent: %s")%elevatorAutoIntent)
	textPrint.tprint(screen, ("UpIntent: %s")%elevatorUpIntent)
	textPrint.tprint(screen, ("DownIntent: %s")%elevatorDownIntent)
	
	textPrint.tprint(screen, ("autoForward: %s")%autoForward)
	textPrint.tprint(screen, ("autoForwardIntent: %s")%autoForwardIntent)
	textPrint.tprint(screen, ("autoForwardReady: %s")%autoForwardReady)
	#
	#
	#######################################################################

	#######################################################################
	# Go ahead and update the screen with what we've drawn.
	pygame.display.flip()
	# Limit to 20 frames per second.
	clock.tick(60)

	#######################################################################
	# We've completed a loop, close the socket so another can be created
	#
	sock.close()

# Close the window and quit.
# If you forget this line, the program will 'hang'
# on exit if running from IDLE.
pygame.quit()
