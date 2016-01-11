"""
  Author: Andrei Stefanescu
  Wyliodrin SRL
"""

from wyliodrin import *


class Button:
  """
    Class used to easy interaction with a hardware button.
    It triggers the callbacks given.
  """
  
  def __init__(self, pin, on_press, on_release):
    pinMode(pin, INPUT)
    self.pin = pin
    self.pressed = False
    self.on_press = on_press
    self.on_release = on_release

  def Update(self, *args, **kwargs):
    v = digitalRead(self.pin)
    if v and not self.pressed:
      self.pressed = True
      self.on_press(args, kwargs)
    elif not v and self.pressed:
      self.pressed = False
      self.on_release(args, kwargs)
      
  def IsPressed(self):
    return self.pressed
