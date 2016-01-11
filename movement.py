"""
  Author: Andrei Stefanescu
  Wyliodrin SRL
"""

from wyliodrin import *
from button import *


def none(*args, **kwargs):
    """
        Blank function as callback for buttons.
    """
  pass

class Movement:
    """
        Class for updating the user's position when pressing buttons.
    """
  
  def __init__(self, rate_press, rate_hold, w, h, pl, pd, pu, pr):
    self.left = Button(pl, none, none)
    self.down = Button(pd, none, none)
    self.up = Button(pu, none, none)
    self.right = Button(pr, none, none)

    self.x = 0
    self.y = 0

    self.rate_press = rate_press    # cells to move when pressed
    self.rate_hold = rate_hold      # cells to move when hold

    self.width = w
    self.height = h

  def Update(self):
    """
        Get new state
    """
    initial = [
                self.left.IsPressed(),
                self.right.IsPressed(),
                self.up.IsPressed(),
                self.down.IsPressed()
              ]

    self.left.Update()
    self.right.Update()
    self.up.Update()
    self.down.Update()

    if self.left.IsPressed():
      if initial[0] == False:
        self.x -= self.rate_press
      else:
        self.x -= self.rate_hold
    
    if self.right.IsPressed():
      if initial[1] == False:
        self.x += self.rate_press
      else:
        self.x += self.rate_hold
    
    if self.up.IsPressed():
      if initial[2] == False:
        self.y += self.rate_press
      else:
        self.y += self.rate_hold
        
    if self.down.IsPressed():
      if initial[3] == False:
        self.y -= self.rate_press
      else:
        self.y -= self.rate_hold

    if self.x < 0:
      self.x = 0
    if self.y < 0:
      self.y = 0
    if self.x >= self.width:
      self.x = self.width - self.rate_press
    if self.y >= self.height:
      self.y = self.height - self.rate_press
