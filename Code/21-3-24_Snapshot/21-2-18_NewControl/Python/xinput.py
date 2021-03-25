
# Xbox 360 Controller class
class xpad:
    def __init__(self, pygameJoystick, deadzone):

        self.ID = pygameJoystick.get_id()

        pygameJoystick.init()

        self.deadzone = deadzone

        # Xbox 360 Controller Name
        self.name = pygameJoystick.get_name()

        # Thumbsticks
        self.left_thumb  = (
            self.dead( pygameJoystick.get_axis(0) ),
            self.dead( pygameJoystick.get_axis(1) )
            )
        self.right_thumb = (
            self.dead( pygameJoystick.get_axis(3) ),
            self.dead( pygameJoystick.get_axis(4) )
            )

        # Triggers
        self.left_trig   = pygameJoystick.get_axis(2)
        self.right_trig  = pygameJoystick.get_axis(5)

        # Buttons
        self.A = pygameJoystick.get_button(0)
        self.B = pygameJoystick.get_button(1)
        self.X = pygameJoystick.get_button(2)
        self.Y = pygameJoystick.get_button(3)

        self.LB = pygameJoystick.get_button(4)
        self.RB = pygameJoystick.get_button(5)

        self.Back = pygameJoystick.get_button(6)
        self.Start = pygameJoystick.get_button(7)

        # The center button
        self.Guide = pygameJoystick.get_button(8)
        
        # When you click the thumbsticks
        self.left_stick = pygameJoystick.get_button(9)
        self.right_stick = pygameJoystick.get_button(10)

        # The directional pad on the 360 controller
        self.dpad = pygameJoystick.get_hat(0)

    # Limits a particular axis
    # by returning its value if it is
    # within the set deadzone. Returns a
    # zero otherwise.
    def dead(self, axis):
        if ( abs(axis) >= self.deadzone ):
            return axis
        
        return 0

    # Turns thumbsticks to Arduino-friendly
    # data...
    def serialized(self):
        packet = ("%.3f,%.3f,%.3f,%.3f")%(
            self.left_thumb[0],
            self.left_thumb[1],
            self.right_thumb[0],
            self.right_thumb[1]
        )

        return packet