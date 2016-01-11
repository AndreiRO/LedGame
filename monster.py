"""
  Author: Andrei Stefanescu
  Wyliodrin SRL
"""

class Monster:
  """
    The evil person in the game. It will simply try
    to get as close as it cans to you.
  """
  def __init__(self, x, y, w, h, rate):
    self.x = x
    self.y = y
    self.w = w
    self.h = h
    self.rate = rate
    
    
  def Update(self, x, y):
    if self.x < x:
      self.x += self.rate
    elif self.x > x:
      self.x -= self.rate
    
    if self.y < y:
      self.y += self.rate
    elif self.y > y:
      self.y -= self.rate