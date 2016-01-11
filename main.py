"""
  Author: Andrei Stefanescu
  Wyliodrin SRL
"""

import os
from wyliodrin import *
from movement import *
from monster import *

from random import randint
from threading import Lock

# because of network communication
# PLAYERS is accesed from multiple threads
lock = Lock()

BID = ""

SER = 0
SRCLCK = 2
RCLCK = 1
MONSTER = 12
CIVILIAN = 13

W = 6         # map width CHANGE AS NEDDED
H = 2         # map height CHANGE AS NEDDED

ROUND = 0     # used to eliminate older messages
PLAYERS = {}  # the global information about all players

# Player(self, rate_press, rate_hold, w, h, pin_l, pin_d, pin_u, pin_r):
player = Movement(1, 0, 6, 2, 11, 10, 9, 8)

# nedded by libwyliodrin
initCommunication()

# activate shift registers and the two red-green leds
pinMode(SER, OUTPUT)
pinMode(RCLCK, OUTPUT)
pinMode(SRCLCK, OUTPUT)
pinMode(MONSTER, OUTPUT)
pinMode(CIVILIAN, OUTPUT)


def clear(v):
  """
    Set each map cell to the given value.
    It sends the value to a shift register.
  """
  global SER, SRCLCK, RCLCK, W, H
  
  digitalWrite(RCLCK, LOW)

  for j in range(H - 1, -1, -1):
    digitalWrite(SER, v)

    for i in range(W - 1, -1, -1):
      digitalWrite(SRCLCK, LOW)
      digitalWrite(SRCLCK, HIGH)

  digitalWrite(RCLCK, HIGH)



def draw_map(x, y):
  """
    Draw the map. Assumes each cell is LOW unless its x is in x param
    and its y is in y param. Output is done with shift registers.
  """
  global SER, SRCLCK, RCLCK, W, H

  digitalWrite(RCLCK, LOW)
  
  for j in range(H - 1, -1, -1):
    for i in range(W - 1, -1, -1):
      flag = False
      
      for it in range(len(x)):
        if x[it] == i and y[it] == j:
          digitalWrite(SER, HIGH)
          flag = True
          break

      if flag == False:
        digitalWrite(SER, LOW)
      
      digitalWrite(SRCLCK, LOW)
      digitalWrite(SRCLCK, HIGH)

  digitalWrite(RCLCK, HIGH)


def main():
  """
    Main method
  """
  global SER, SRCLCK, RCLCK, W, H, PLAYERS, BID, lock, player, ROUND

  # def __init__(self, x, y, w, h, rate):
  monster = Monster(W - 1, H - 1, W, H, 1)

  s = raw_input("single/multi ?\n")

  if s == "single":
    """
      Start single player with only a monster.
    """
    print "Starting singleplayer. Enjoy :)"

    ct = 0
    while True:
      clear(LOW)
      player.Update()

      # we use a counter instead of a bigger delay
      # to respond quicker to input
      if ct >= 100:
        ct = 0
        monster.Update(player.x, player.y)
      
      draw_map([player.x, monster.x], [player.y, monster.y])
      ct = ct + 1
  
      if player.x == monster.x and player.y == monster.y:
        # flash the leds and reposition player and monster
        led_restart()
        monster.x = W - 1
        monster.y = H - 1
        player.x = 0
        player.y = 0

      delay(10)

  else:
    print "Starting multiplayer"
    BID = raw_input("Enter Board ID:\n")
    i = raw_input("master/slave?\n")
  
    if i == "master":
      # master updates map and sends it to its slaves
      PLAYERS[BID] = { "x" : -1, "y": -1, "alive": False, "monster" : True}
      openConnection('ack', getAck)
      openConnection('coords', getSlaveCoords)

      raw_input("Type to start game\n")
      
      print "Starting game..."
      initGame()
      
      while True:
        print "Round: ", ROUND
        try:
          lock.acquire()
          player.x = PLAYERS[BID]['x']
          player.y = PLAYERS[BID]['y']
        finally:
          lock.release()

        while gameOn():
          player.Update()

          try:
            lock.acquire()
            PLAYERS[BID]['x'] = player.x
            PLAYERS[BID]['y'] = player.y
        
            # check map for collisions
            for p1 in PLAYERS.keys():
              if PLAYERS[p1]['alive'] and PLAYERS[p1]['monster']:
                for p2 in PLAYERS.keys():
                  if p1 == p2 or not PLAYERS[p2]['alive']:
                    continue
            
                  if PLAYERS[p1]['x'] == PLAYERS[p2]['x'] and PLAYERS[p1]['y'] == PLAYERS[p2]['y']:
                    PLAYERS[p2]['alive'] = False
                    PLAYERS[p1]['alive'] = not PLAYERS[p2]['monster']

            # send coords to slaves
            sendCoords()
            
            # draw map
            xcoord = []
            ycoord = []
            
            for p in PLAYERS.keys():
              if PLAYERS[p]['alive']:
                xcoord.append(PLAYERS[p]['x'])
                ycoord.append(PLAYERS[p]['y'])

            draw_map(xcoord, ycoord)
            delay(10)
        
          finally:
            lock.release()
        

        try:
          lock.acquire()
          
          for p in PLAYERS.keys():
            sendMessage(p, 'end', json.dumps('Ended game'))
          #print "Game ended", PLAYERS
          delay(200)
          led_restart()        
      
        finally:
          lock.release()
        initGame()
    else:
      mid = raw_input("Enter Master board id:")
      PLAYERS[BID] = { "x" : -1, "y": -1, "alive": False, "monster" : True}
      sendMessage(mid, 'ack', json.dumps('Acknoledgement'))
      print "Acknoledgement sent"
      
      openConnection('coords', getStatus)
      openConnection('end', gameEnded)
      openConnection('init', slaveInit)
      
      while True:
        # draw map
        try:
          lock.acquire()
          xcoord = []
          ycoord = []
          
          if PLAYERS[BID]['alive']:
            # respond to input
            player.Update()

            # update coordinates
            PLAYERS[BID]['x'] = player.x
            PLAYERS[BID]['y'] = player.y
          
            # send new values
            sendMessage(mid,
                        'coords',
                        json.dumps({
                                    'x' : player.x,
                                    'y' : player.y,
                                    'round' : ROUND
                                    }))

          # get all alive players' coordinates
          # and update map
          for p in PLAYERS.keys():
            if PLAYERS[p]['alive']:
              xcoord.append(PLAYERS[p]['x'])
              ycoord.append(PLAYERS[p]['y'])

          # draw it  
          draw_map(xcoord, ycoord)
          delay(5)
        finally:
          lock.release()


def initGame():
  """
    Function that initializes game state. Called each new round.
  """
  global W, H, PLAYERS, lock, player, ROUND

  try:
    lock.acquire()
    
    # to filter old messages
    ROUND += 1

    i = 0
    j = 0

    m = len(PLAYERS.keys()) / 2
    temp = PLAYERS.keys()
    ct = 0
    
    # first populate monsters
    while m > 0:
      ind = randint(0, m - 1)
      PLAYERS[temp[ind]]['monster'] = True
      m -= 1
      del temp[ind]
    
    # then make the others civillians
    for p in temp:
      PLAYERS[p]['monster'] = False
    
    while j < H and ct < len(PLAYERS.keys()):
      i = 0
      while i < W and ct < len(PLAYERS.keys()):
        PLAYERS[PLAYERS.keys()[ct]]['x'] = i
        PLAYERS[PLAYERS.keys()[ct]]['y'] = j
        PLAYERS[PLAYERS.keys()[ct]]['alive'] = True
        i += 2
        ct += 1
      j += 2
      
    # update master player coordinates
    player.x = PLAYERS[BID]['x']
    player.y = PLAYERS[BID]['y']

    # print initial coordinates
    displayInitialCoords(PLAYERS[BID]['x'], PLAYERS[BID]['y'])
    digitalWrite(CIVILIAN, LOW)
    digitalWrite(MONSTER, LOW)
    
    # draw role
    if PLAYERS[BID]['monster']:
      digitalWrite(MONSTER, HIGH)
    else:
      digitalWrite(CIVILIAN, HIGH)
    
    for p in PLAYERS.keys():
      sendMessage(
                    p, 
                    'init', 
                    json.dumps({'PLAYERS' : PLAYERS, 'round' : ROUND})
                  )
  finally:
    lock.release()


def slaveInit(__sender, __chanel, __error, __message):
  """
    Initialize slave. Called each new round.
  """
  global PLAYERS, lock, player, ROUND
  
  try:
    lock.acquire()
    print "Slave Init"
    
    payload = json.loads(__message)
    
    PLAYERS = payload['PLAYERS']
    ROUND = payload['round']
    
    digitalWrite(CIVILIAN, LOW)
    digitalWrite(MONSTER, LOW)
    
    player.x = PLAYERS[BID]['x']
    player.y = PLAYERS[BID]['y']
    
    # draw role
    if PLAYERS[BID]['monster']:
      digitalWrite(MONSTER, HIGH)
    else:
      digitalWrite(CIVILIAN, HIGH)

    # draw initial coordinates
    displayInitialCoords(PLAYERS[BID]['x'], PLAYERS[BID]['y'])

  finally:
    lock.release()

def led_restart():
  """
    Flashy led pattern that tells the end of a round.
  """
  clear(HIGH)
  delay(3000)
  
  for i in range(3):
    clear(LOW)
    delay(500)
    clear(HIGH)
    delay(500)


def gameOn():
  """
    Determine wheter there are more than 2 monsters or one monster and a civillian
  """
  global PLAYERS, lock
  
  ok = True
  
  try:
    lock.acquire()

    monsters = [x for x in PLAYERS.keys() if PLAYERS[x]['monster'] and PLAYERS[x]['alive']]
    civilians = [x for x in PLAYERS.keys() if not PLAYERS[x]['monster'] and PLAYERS[x]['alive']]
    
    if len(monsters) != 2 && (len(civilians) != 1 and len(monsters) == 1):
      ok = False    

  finally:
    lock.release()
  
  return ok


def displayInitialCoords(x, y):
  clear(LOW)
  draw_map([x,], [y,])
  delay(1000)
  clear(LOW)
  
  
def getAck(__sender, __channel, __error, __message):
  """
    Called when new slave enters the game.
  """
  global PLAYERS, lock

  try:
    lock.acquire()
    PLAYERS[__sender] = { "x" : 0, "y": 0, "alive": True, "monster" : True}      
    print "Player: " + __sender + " is online"  
  finally:
    lock.release()


def getSlaveCoords(__sender, __channel, __error, __message):
  """
    Update slave coordinates in master's dictionary after receving them.
  """
  global PLAYERS, lock

  if __sender == BID:
    return False

  try:
    lock.acquire()
    #print "Got slave coords", __sender
    p = json.loads(__message)
    
    if p['round'] < ROUND:
      # ignore older rounds messages
      return False
    
    if p['x'] == -1:
      return False
      
    PLAYERS[__sender]['x'] = p['x']
    PLAYERS[__sender]['y'] = p['y']
  finally:
    lock.release()
  
  
def getStatus(__sender, __channel, __error, __message):
  """
    Updates all data for a slave.
  """
  global PLAYERS, lock

  if BID == __sender:
    return False

  try:
    lock.acquire()
    PLAYERS  = json.loads(__message)
  finally:
    lock.release()
  print "Got status"


def gameEnded(__sender, __channel, __error, __message):
  """
    For slaves display game end.
  """
  global PLAYERS, lock, player

  try:
    lock.acquire()
    led_restart()
    print "Game ended"

  finally:
    lock.release()

  
def sendCoords():
  """
    For Master, update slaves with their coordinates.
  """
  global PLAYERS, lock

  try:
    lock.acquire
    for p in PLAYERS.keys():
      sendMessage(
                    p, 
                   'coords', 
                    json.dumps(PLAYERS)
                 )
  finally:
    lock.release



if __name__ == "__main__":
  main()  