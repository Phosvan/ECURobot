import xinput
import pygame
import socket
import time
import os
import time
import curses
import math

#
# Configure TCP params
#
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv_address = srv_address = ('', 32768) #bind to local host
sock.setblocking(0)


def send_xpad_info(info):
    sock.sendto(bytes(info, 'utf-8'), srv_address)

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
# Configure beautiful OSD
#

bannertxt = (" _    _ ______ _      __  __ \n"
    "| |  | |  ____| |    |  \/  |\n"
    "| |__| | |__  | |    | \  / |\n"
    "|  __  |  __| | |    | |\/| |\n"
    "| |  | | |____| |____| |  | |\n"
    "|_|  |_|______|______|_|  |_|\n"
    "\nCreated by the ECU ATMAE Chapter\n")

def welcomeMsg(stdscr, winW, winH):
    #center text
    
    stdscr.addstr(0, 0, bannertxt)
    stdscr.refresh()

### Attempt to bind to TCP Socket, print updates to CLI ###
def tcpSetup(stdscr):
    try:
        sock.bind(srv_address)
        sock.listen(1)
    except:
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr("Socket failed to open. This may have occurred due to a crash.\n\n"
            "When counter expires, the program will exit and you will need to \nrelaunch this script\n\n\n"
            "Closing in: ")
        expiry = 20
        while (expiry != 0):
            stdscr.addstr(str(expiry).zfill(2))
            curY, curX = stdscr.getyx()
            curX -= 2
            stdscr.move(curY, curX)
            stdscr.refresh()
            time.sleep(1)
            expiry-=1
        raise Exception('Closed due to inability to open socket. Relaunch script.')

    stdscr.addstr("Socket opened successfully.")
    stdscr.refresh()
    time.sleep(3)
    stdscr.clear()
    stdscr.refresh()

### Configure windows within CLI ###
class windowHeader:
    def __init__(self, stdscr, winW, winH):
        self.header = curses.newwin(1,winW,0,0)
        headerTxt = (str(get_ip()) + ":" + str(srv_address[1]))
        self.header.addstr(0,int(((winW/2)-(len(headerTxt)/2))),headerTxt)

    def refresh(self,stdscr):
        self.header.refresh()
        stdscr.refresh()

class sysStatusWindow:
    headerW = 0
    headerH = 0
    bodyTextStartCol = 0
    def __init__(self, stdscr, winW, winH):
        self.header = curses.newwin(1, int(winW/2), 1, int(winW/2))
        self.header.attron(curses.color_pair(4))
        self.header.bkgd(curses.color_pair(4))
        headerH, headerW = self.header.getmaxyx()
        bodyTextStartCol = headerW + 1
        self.body = curses.newwin(int(winH/2)-2, int(winW/2), 2, int(winW/2)+1)
        self.paintLBorder()
        self.body.attron(curses.color_pair(3))
        self.body.bkgd(curses.color_pair(3))
        headerTxt = "SYSTEM STATUS"
        self.header.addstr(0, int(((headerW/2)-(len(headerTxt)/2))), headerTxt)

    def paintLBorder(self):
        bodyHMax, bodyWMax = self.body.getmaxyx()
        for y in range(0, bodyHMax):
            self.body.attron(curses.color_pair(4))
            self.body.addstr(y, 0, " ")

    def refresh(self, stdscr):
        self.header.refresh()
        self.body.refresh()

class coordWindow:
    headerW = 0
    headerH = 0
    bodyTextStartCol = 0
    def __init__(self, stdscr, winW, winH):
        self.header = curses.newwin(1, int(winW/2), int(winH/2), int(winW/2))
        self.header.attron(curses.color_pair(4))
        self.header.bkgd(curses.color_pair(4))
        headerH, headerW = self.header.getmaxyx()
        bodyTextStartCol = headerW + 1
        self.body = curses.newwin(int(winH/2)+1, int(winW/2), int(winH/2)+1, int(winW/2)+1)
        self.paintLBorder()
        self.body.attron(curses.color_pair(3))
        self.body.bkgd(curses.color_pair(3))
        headerTxt = "COORDINATE PLANE"
        self.header.addstr(0, int(((headerW/2)-(len(headerTxt)/2))), headerTxt)

    def paintLBorder(self):
        bodyHMax, bodyWMax = self.body.getmaxyx()
        for y in range(0, bodyHMax):
            self.body.attron(curses.color_pair(4))
            self.body.addstr(y, 0, " ")

    def refresh(self, stdscr):
        self.header.refresh()
        self.body.refresh()

class dataPIDWindow:
    headerW = 0
    headerH = 0
    bodyTextStartCol = 0
    def __init__(self, stdscr, winW, winH):
        self.header = curses.newwin(1, int(winW/2), int(winH/2), 0)
        self.header.attron(curses.color_pair(4))
        self.header.bkgd(curses.color_pair(4))
        headerH, headerW = self.header.getmaxyx()
        bodyTextStartCol = headerW + 1
        self.body = curses.newwin(int(winH/2), int(winW/2), int(winH/2)+1, 0)
        self.body.attron(curses.color_pair(3))
        self.body.bkgd(curses.color_pair(3))
        headerTxt = "DATA PIDs"
        self.header.addstr(0, int(((headerW/2)-(len(headerTxt)/2))), headerTxt)

    def refresh(self, stdscr):
        self.header.refresh()
        self.body.refresh()

class topLeftWindow:
    headerW = 0
    headerH = 0
    bodyTextStartCol = 0
    def __init__(self, stdscr, winW, winH):
        self.header = curses.newwin(1, int(winW/2), 1, 0)
        self.header.attron(curses.color_pair(4))
        self.header.bkgd(curses.color_pair(4))
        headerH, headerW = self.header.getmaxyx()
        bodyTextStartCol = headerW + 1
        self.body = curses.newwin(int(winH/2)-2, int(winW/2), 2, 0)
        self.body.attron(curses.color_pair(3))
        self.body.bkgd(curses.color_pair(3))
        headerTxt = " - "
        self.header.addstr(0, int(((headerW/2)-(len(headerTxt)/2))), headerTxt)

    def refresh(self, stdscr):
        self.header.refresh()
        self.body.refresh()


#
# watchDog, used to keep track of if a bot has connected
# and how long it has been connected
#
class watchDog:

    def __init__(self):
        self.timeInstantiated = time.ctime()
        self.prevConnected = False
        self.lastSeen = "-"

    def update(self):
        self.prevConnected = True
        self.lastSeen = time.ctime()


#Data headers
def dataPIDConstructor(npad):
    ABXY = ( "A, B, X, Y:          %i, %i, %i, %i\n"%(npad.A, npad.B, npad.X, npad.Y))
    Bump = ( "Bumpers L/R:         %i, %i\n"%(npad.LB, npad.RB))
    Util = ( "Back, Start, Guide:  %i, %i, %i\n"%(npad.Back, npad.Start, npad.Guide))
    Stck = ( "Sticks L/R:          %i, %i\n"%(npad.left_stick, npad.right_stick))
    DPad = ( "DPad X/Y:            %i, %i\n"%(npad.dpad[0], npad.dpad[1]))
    ThumL = ( "Thumbstick L (X,Y):  %.3f, %.3f\n"%(npad.left_thumb[0], npad.left_thumb[1]))
    ThumR = ( "Thumbstick R (X,Y):  %.3f, %.3f"%(npad.right_thumb[0], npad.right_thumb[1]))
    return str(ABXY + Bump + Util + Stck + DPad + ThumL + ThumR)

def systemStatusConstructor(watchDogObject):
    sessionStartTime = ( " Session Start Time: \n    " + watchDogObject.timeInstantiated + "\n")
    activeTxt = ( " Previously Connected: " + str(watchDogObject.prevConnected) + "\n")
    lastSeenTxt = ( " Time Last Seen: \n    " + watchDogObject.lastSeen + "\n")
    return str( sessionStartTime + activeTxt + lastSeenTxt)


def main(stdscr):
    curses.curs_set(0) #disable blinking cursor
    winH, winW = stdscr.getmaxyx()
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_MAGENTA) #base
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED) #error
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_MAGENTA) #body
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_CYAN) #window headers
    stdscr.attron(curses.color_pair(1))
    stdscr.bkgd(curses.color_pair(1))
    welcomeMsg(stdscr, winW, winH)
    tcpSetup(stdscr)
    
    listener = watchDog()


    headW = windowHeader(stdscr, winW, winH)
    statusW = sysStatusWindow(stdscr, winW, winH)
    coordW = coordWindow(stdscr, winW, winH)
    dataPIDW = dataPIDWindow(stdscr, winW, winH)
    logoW = topLeftWindow(stdscr, winW, winH)
    headW.refresh(stdscr)
    statusW.refresh(stdscr)
    coordW.refresh(stdscr)
    dataPIDW.refresh(stdscr)
    logoW.body.addstr(0,0, bannertxt)
    logoW.refresh(stdscr)

    while(1):

        try:
            connection, client_address = sock.accept()
            listener.update()
        except:
            pass

        npad = xinput.xpad(pygame.joystick.Joystick(0), 0.18)
        xname = npad.name
        dataPIDW.body.addstr(0,0,dataPIDConstructor(npad))
        dataPIDW.refresh(stdscr)
        statusW.body.attron(curses.color_pair(3)) # MORE JANK
        statusW.body.addstr(0,0,systemStatusConstructor(listener))
        statusW.paintLBorder() #THIS IS SO JANK
        statusW.refresh(stdscr)

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

        try:
            connection.sendall(bytes(packet, 'utf-8'))
        except:
            pass


#
# Setup Pygame Params, launch app wrapper
#
pygame.init()
pygame.joystick.init()
curses.wrapper(main)