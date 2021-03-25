import xinput
import pygame
import socket
import time

srv_address = ('', 32768)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(srv_address)
sock.listen(1)

def send_xpad_info(info):
	sock.sendto(bytes(info, 'utf-8'), srv_address)


pygame.init()

pygame.joystick.init()

screen = pygame.display.set_mode((500, 700))

pygame.display.set_caption("TCP Xbox 360 Controller Server")

sendThreshold = 0.0

while True:
	connection, client_address = sock.accept()
	#
	# EVENT PROCESSING STEP
	#
	# Possible joystick actions: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
	# JOYBUTTONUP, JOYHATMOTION
	for event in pygame.event.get(): # User did something.
		if event.type == pygame.QUIT: # If user clicked close.
			done = True # Flag that we are done so we exit this loop.
		elif event.type == pygame.JOYBUTTONDOWN:
			print("Joystick button pressed.")
		elif event.type == pygame.JOYBUTTONUP:
			print("Joystick button released.")

	npad = xinput.xpad(pygame.joystick.Joystick(0), 0.18)

	xname = npad.name

	sticks = npad.serialized()

	buttons = [
		npad.A,
		npad.B,
		npad.X,
		npad.Y,
		npad.LB,
		npad.RB,
		npad.Back,
		npad.Start,
		npad.Guide,
		npad.left_stick,
		npad.right_stick,
		npad.dpad[0],
		npad.dpad[1]
	]

	str_buttons = [ ('%i,')%(buttons[x]) for x in range(len(buttons)-1) ]
	str_buttons.append( ('%i')%(buttons[len(buttons)-1]) )

	total_buttons = ''.join(str_buttons)

	packet = '<' + sticks + ',' + total_buttons + '>'

	#print(packet)
	connection.sendall(bytes(packet, 'utf-8'))

	"""if (npad.Back == 1):
		send_xpad_info('QUIT')
		break"""

	pygame.display.flip()

pygame.quit()
