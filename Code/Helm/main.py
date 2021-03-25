import xinput
import pygame
import socket
import time
import os
from datetime import datetime
import urwid

srv_address = ('', 32768)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(srv_address)
sock.listen(1)

def send_xpad_info(info):
	sock.sendto(bytes(info, 'utf-8'), srv_address)

#
# Set up CLI handlers
#
def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


#
# Set up PyGame for Xbox Input
#
pygame.init()
pygame.joystick.init()

#
# Format CLI, Print welcome
#
print("Listening for Pegleg at:",get_ip(),srv_address[1])



while True:
	connection, client_address = sock.accept()
	lastSeen = datetime.now().strftime("%H:%M:%S")
	print("Last successful update at", lastSeen, "for client", client_address[0], end="\r")


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



pygame.quit()
