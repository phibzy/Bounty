#!/usr/bin/env python

# bounty.py
# COMP3411 - Assignment 3
# Chris Phibbs and Callum Howard 2015

import math
import socket
import sys
from socket import error as SocketError
from Queue import Queue
import time
import copy
from termcolor import colored  #TODO remove before submitting

class GameState(object):
    'GameState class stores state of Bounty game'

    PORT = 31415
    MAX_MOVES = 10000
    BOARD_DIM = 30
    BOARD_SIZE = BOARD_DIM * BOARD_DIM
    VIEW_DIM = 5
    VIEW_SIZE = VIEW_DIM * VIEW_DIM
    FOG_CHAR = '+'#u'\u2588'

    FEATURES = {
        'player':   '^',
        'dynamite': 'd',
        'tree':     'T',
        'boat':     'B',
        'water':    '~',
        'wall':     '*',
        'axe':      'a',
        'gold':     'g',
        'land':     ' ',
        'edge':     '.',
        'fog':      FOG_CHAR
    }

    MOVES = {
        'forward':  'f',
        'left':     'l',
        'right':    'r',
        'chop':     'c',
        'blast':    'b'
    }

    CARDINAL = {
        'north':    0,
        'east':     1,
        'south':    2,
        'west':     3
    }

    DIRECTIONS = {
        'left':     3,  # same as -1 but works with mod
        'right':    1
    }

    # Constructor method for GameState class
    def __init__(self):
        self.turn_num = 0
        self.board = Board()
        self.current_view = []

        self.directory = {
            'gold':     None,
            'boat':     [],
            'dynamite': [],
            'axe':      None,
            'tree':     []
        }

        # Establishes TCPIP connection on localhost at specified port
        portNumber = int(sys.argv[2])
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = ('localhost', portNumber)
        self.sock.connect(address)

        try:
            received_data = ""
            data_stream = ""
            while len(received_data) != 24:
                data_stream = self.sock.recv(4092)
                if len(data_stream) == 0:
                    break
                received_data += data_stream
            i = 0
            received_data = received_data[:12]+"^"+received_data[12:]
            agent_view = ""
            while (i < 25):
                agent_view = agent_view+received_data[i]
                i += 1
        except SocketError:
            self.sock.close()
        self._convertString2List(agent_view)

        self._storeView(self.board.START_LOCATION, Agent.INIT_ROTATION)

    ### getters
    def getTurn(self):
        return self.turn_num


    ### setters
    def _nextTurn(self):
        if self.turn_num < GameState.MAX_MOVES:
            self.turn_num += 1
        else:
            print 'Game Lost.'
            exit()

    def _orientate(self, rotation):
        rotated_view = self.current_view
        for num in range(rotation):
            # rotate view clockwise
            rotated_view = zip(*rotated_view[::-1])

        return rotated_view


    # updates the internal representation of the board with the agent's current view
    def _storeView(self, agent_location, agent_rotation):
        # rotate current view to universal orientation
        rotated_view = self._orientate(agent_rotation)

        # use agent location to determin which rows and columns of the board to update
        offset = int(math.floor(GameState.VIEW_DIM / 2))  # floor because of zero indexing

        # set board cursor to top left of the view
        row_start = agent_location[1] - offset
        row_end = row_start + GameState.VIEW_DIM
        col_start = agent_location[0] - offset
        col_end = col_start + GameState.VIEW_DIM

        # store current view into board row by row, col by col
        for i, row in enumerate(range(row_start, row_end)):
            for j, col in enumerate(range(col_start, col_end)):
                self.board.board[row][col] = rotated_view[i][j]
                #print "before location check in", self.board.getLocation((col, row))
                if self.board.getLocation((col, row)) == GameState.FEATURES['gold']:
                    if self.directory['gold'] == None:
                        self.setGoldLocation((col, row))
                elif self.board.getLocation((col, row)) == GameState.FEATURES['axe']:
                    if self.directory['axe'] == None:
                        self.setAxeLocation((col, row))
                elif self.board.getLocation((col, row)) == GameState.FEATURES['dynamite']:
                    if (col, row) not in self.directory['dynamite']:
                        self.setDynamiteLocation((col, row))
                elif self.board.getLocation((col, row)) == GameState.FEATURES['tree']:
                    if (col, row) not in self.directory['tree']:
                        self.setTreeLocation((col, row))
                elif self.board.getLocation((col, row)) == GameState.FEATURES['boat']:
                    if (col, row) not in self.directory['boat']:
                        self.setBoatLocation((col, row))
                #print " location check in", self.board.getLocation((col, row))


    ### other methods
    def printBoard(self):
        self.board.printBoard()
        pass
        #time.sleep(0.05)
        #raw_input()


    def sendMove(self, move, agent_location, agent_rotation):

        # sends the chosen move to the bounty server
        self.sock.sendall(move)

        try:
            received_data = ""
            data_stream = ""
            while len(received_data) != 24:
                data_stream = self.sock.recv(4092)
                if len(data_stream) == 0:
                    break
                received_data += data_stream
            i = 0
            markers = [u'\u25B2', u'\u25B6', u'\u25BC', u'\u25C0']
            received_data = received_data[:12] + markers[agent_rotation] + received_data[12:]
            agent_view = ""
            while (i < GameState.VIEW_SIZE):
                agent_view = agent_view+received_data[i]
                i += 1
        except (SocketError, IndexError):
            self.sock.close()
            self._nextTurn()
            print "Game Won in", self.getTurn(), "moves."
            exit()

        self._convertString2List(agent_view)

        # update internal representation of the board
        self._storeView(agent_location, agent_rotation)
        self._nextTurn()
        self.printBoard()

    def _convertString2List(self, string):
        i = 0
        j = 0

        self.current_view = []
        while (i < GameState.VIEW_DIM):
            self.current_view.append([])
            i+=1

        i = 0

        while (j < GameState.VIEW_SIZE):
            if (j % GameState.VIEW_DIM  == 0 and j != 0):
                i+=1
            self.current_view[i].append(string[j])
            j+=1

    def setGoldLocation(self, location):
        if self.directory['gold'] == None:
            self.directory['gold'] = location

    def setNoneGoldLocation(self):
        self.directory['gold'] = None


    def setAxeLocation(self, location):
        if self.directory['axe'] == None:
            self.directory['axe'] = location

    def setNoneAxeLocation(self):
        self.directory['axe'] = None

    def setDynamiteLocation(self, location):
        self.directory['dynamite'].append(location)

    def setNoneBoatLocation(self, location):
        self.directory['boat'].remove(location)

    def setBoatLocation(self, location):
        self.directory['boat'].append(location)

    def removeDynamiteFromList(self, location):
        self.directory['dynamite'].remove(location)

    def getGoldLocation(self):
        return self.directory['gold']

    def getAxeLocation(self):
        return self.directory['axe']

    def getDynamiteLocations(self):
        return self.directory['dynamite']

    def getBoatLocation(self):
        return self.directory['boat']

    def setTreeLocation(self, location):
        self.directory['tree'].append(location)

    def getTreeLocations(self):
        return self.directory['tree']

    def removeTreeFromList(self, location):
        self.directory['tree'].remove(location)

class Board(object):
    'Board class for internal representation of game board'

    START_LOCATION = (GameState.BOARD_DIM, GameState.BOARD_DIM)


    def __init__(self):
        # make internal board twice as big to guarantee enough space
        side_length = 2 * GameState.BOARD_DIM

        # board is a list of lists initialised to fog
        self.board = []
        for i in range(side_length):
            row = []
            for j in range(side_length):
                row.append(GameState.FEATURES['fog'])
            self.board.append(row)

        self.overlay = []


    # location is a tuple of form (x, y)
    # returns coordinate above
    def getUp(self, location):
        return (location[0], location[1] - 1)


    # returns coordinate to right
    def getRight(self, location):
        return (location[0] + 1, location[1])


    # returns coordinate below
    def getDown(self, location):
        return (location[0], location[1] + 1)


    # returns coordinate to left
    def getLeft(self, location):
        return (location[0] - 1, location[1])


    # returns the contents of the location
    def getLocation(self, location):
        return self.board[location[1]][location[0]]


    # returns adjacent locations that are in the map
    def getAdjacent(self, location):
        valid_adjacent = []
        all_adjacent = {
            'up':       self.getUp(location),
            'right':    self.getRight(location),
            'down':     self.getDown(location),
            'left':     self.getLeft(location)
        }

        for direction, coordinate in all_adjacent.iteritems():
            if all_adjacent[direction] != GameState.FEATURES['edge']:
                valid_adjacent.append(coordinate)

        return valid_adjacent


    def getAdjOnLand(self, location, has_axe, num_dynamite):
        land_adjacent = []
        all_adjacent = self.getAdjacent(location)
        for coordinate in all_adjacent:
            if self.isLand(coordinate):
                land_adjacent.append(coordinate)
            elif self.isTree(coordinate) and has_axe:
                land_adjacent.append(coordinate)
            elif self.isWall(coordinate) and num_dynamite > 0:
                land_adjacent.append(coordinate)
            elif self.isAxe(coordinate):
                land_adjacent.append(coordinate)
            elif self.isDynamite(coordinate):
                land_adjacent.append(coordinate)
            elif self.isGold(coordinate):
                land_adjacent.append(coordinate)
            elif self.isBoat(coordinate):
                land_adjacent.append(coordinate)
        return land_adjacent


    def getAdjAndUnexplored(self, location, has_axe, num_dynamite):
        land_adjacent = []
        all_adjacent = self.getAdjacent(location)
        for coordinate in all_adjacent:
            if self.isLand(coordinate):
                land_adjacent.append(coordinate)
            elif self.isTree(coordinate) and has_axe:
                land_adjacent.append(coordinate)
            elif self.isWall(coordinate) and num_dynamite > 0:
                land_adjacent.append(coordinate)
            elif self.isAxe(coordinate):
                land_adjacent.append(coordinate)
            elif self.isDynamite(coordinate):
                land_adjacent.append(coordinate)
            elif self.isGold(coordinate):
                land_adjacent.append(coordinate)
            elif self.isBoat(coordinate):
                land_adjacent.append(coordinate)
            elif self.isFog(coordinate):
                land_adjacent.append(coordinate)
        return land_adjacent


    def getAdjOnWater(self, location, has_axe, num_dynamite):
        water_adjacent = []
        all_adjacent = self.getAdjacent(location)
        for coordinate in all_adjacent:
            if self.isWater(coordinate):
                water_adjacent.append(coordinate)
            elif self.isLand(coordinate):
                water_adjacent.append(coordinate)
            elif self.isTree(coordinate) and has_axe:
                water_adjacent.append(coordinate)
            elif self.isWall(coordinate) and num_dynamite > 0:
                water_adjacent.append(coordinate)
            elif self.isAxe(coordinate):
                water_adjacent.append(coordinate)
            elif self.isDynamite(coordinate):
                water_adjacent.append(coordinate)
            elif self.isGold(coordinate):
                water_adjacent.append(coordinate)
            elif self.isBoat(coordinate):
                water_adjacent.append(coordinate)
        return water_adjacent


    def isDynamite(self, location):
        return self.getLocation(location) == GameState.FEATURES['dynamite']


    def isTree(self, location):
        return self.getLocation(location) == GameState.FEATURES['tree']


    def isBoat(self, location):
        return self.getLocation(location) == GameState.FEATURES['boat']


    def isWater(self, location):
        return self.getLocation(location) == GameState.FEATURES['water']


    def isWall(self, location):
        return self.getLocation(location) == GameState.FEATURES['wall']


    def isAxe(self, location):
        return self.getLocation(location) == GameState.FEATURES['axe']


    def isGold(self, location):
        return self.getLocation(location) == GameState.FEATURES['gold']


    def isLand(self, location):
        return self.getLocation(location) == GameState.FEATURES['land']


    def isEdge(self, location):
        return self.getLocation(location) == GameState.FEATURES['land']


    def isFog(self, location):
        return self.getLocation(location) == GameState.FEATURES['fog']


    # returns a list of cardinal directions
    def getShortestPath(self, origin, destination, has_axe, num_dynamite):
        path = []
        markers = ['^', '>', 'v', '<']
        max_path_length = GameState.BOARD_SIZE
        parent = self.bfs(origin, has_axe, num_dynamite)
        current = destination

        #DEBUG
        path_map = copy.deepcopy(self.overlay) #bfs must be called before here

        loop_count = 0
        while current != origin and loop_count < max_path_length:
            prev = current
            current = parent[ current[1] ][ current[0] ]

            # if no path can be found return empty list
            if current == (0, 0):
                return []
            path.append(self.directionAdjacent(current, prev))
            loop_count += 1

            #DEBUG
            #print path
            for direction in path:
                path_map[ current[1] ][ current[0] ] = colored(markers[direction], 'green', 'on_grey')
            self.overlay = path_map
            self.printBoard()
            #self.printBoard(path_map)
#            for row in path_map:
#                print ' '.join(row)
            #time.sleep(0.02)  #TODO remove before submitting
        self.overlay = self.board
        time.sleep(0.5)  #TODO remove before submitting
        #raw_input()

        return list(reversed(path))


    def getShortestExplorationPath(self, origin, destination, has_axe, num_dynamite):
        path = []
        markers = ['^', '>', 'v', '<']
        max_path_length = GameState.BOARD_SIZE
        parent = self.bfs(origin, has_axe, num_dynamite)
        current = destination

        #DEBUG
        path_map = copy.deepcopy(self.board)

        loop_count = 0
        while current != origin and loop_count < max_path_length:
            prev = current
            current = parent[ current[1] ][ current[0] ]

            # if no path can be found return empty list
            if current == (0, 0):
                return []
            path.append(self.directionAdjacent(current, prev))
            loop_count += 1

            #DEBUG
            #print path
            for direction in path:
                path_map[ current[1] ][ current[0] ] = colored(markers[direction], 'cyan', 'on_grey')
#            for row in path_map:
#                print ' '.join(row)
            self.overlay = path_map
            self.printBoard()
            #self.printBoard(path_map)
#            time.sleep(0.2)  #TODO remove before submitting
        raw_input()

        return list(reversed(path))


    # Breadth First Search on what has been seen in internal representation of board
    def bfs(self, origin, has_axe, num_dynamite):
        frontier = Queue()
        frontier.put(origin)
        side_length = 2 * GameState.BOARD_DIM
        UNEXPLORED = (0, 0)
        #markers = ['^', '>', 'v', '<']
        markers = ['v', '<', '^', '>']
        # contains the location that bfs came from, otherwise UNEXPLORED
        parent = []
        for i in range(side_length):
            row = []
            for j in range(side_length):
                row.append(UNEXPLORED)
            parent.append(row)

        adj_map = copy.deepcopy(self.board)

        #TODO implement dynamite

        while not frontier.empty():
            current = frontier.get()
            for adjacent in self.getAdjOnLand(current, has_axe, num_dynamite):  #TODO implement water
                if parent[ adjacent[1] ][ adjacent[0] ] == UNEXPLORED:
                    frontier.put(adjacent)
                    parent[ adjacent[1] ][ adjacent[0] ] = current
                    adj_map[ adjacent[1] ][ adjacent[0] ] = colored(markers[self.directionAdjacent(current, adjacent)], 'blue', 'on_grey')

        self.overlay = adj_map
        #self.printBoard(adj_map)
#        for line in adj_map:
#            print ' '.join(line)
#        raw_input()

        return parent


    def getNearestUnexplored(self, origin, has_axe, num_dynamite):
        frontier = Queue()
        frontier.put(origin)
        side_length = 2 * GameState.BOARD_DIM
        UNEXPLORED = (0, 0)
        #markers = ['^', '>', 'v', '<']
        markers = ['v', '<', '^', '>']
        # contains the location that bfs came from, otherwise UNEXPLORED
        parent = []
        for i in range(side_length):
            row = []
            for j in range(side_length):
                row.append(UNEXPLORED)
            parent.append(row)

        adj_map = copy.deepcopy(self.board)

        #TODO implement dynamite

        while not frontier.empty():
            current = frontier.get()

            if self.getLocation(current) == GameState.FEATURES['fog']:
                print 'CURRENT LOCATION: |' + self.getLocation(current) + '|'
                #raw_input()
                return current

            for adjacent in self.getAdjAndUnexplored(current, has_axe, num_dynamite):  #TODO implement water
                if parent[ adjacent[1] ][ adjacent[0] ] == UNEXPLORED:
                    frontier.put(adjacent)
                    parent[ adjacent[1] ][ adjacent[0] ] = current
                    adj_map[ adjacent[1] ][ adjacent[0] ] = colored(markers[self.directionAdjacent(current, adjacent)], 'blue')

            for line in adj_map:
                print ' '.join(line)
            print 'CURRENT LOCATION: |' + self.getLocation(current) + '|'
            #raw_input()

        return None


    def printBoard(self):
        markers = [u'\u25B2', u'\u25B6', u'\u25BC', u'\u25C0']
        buff_out = []
        if self.overlay:
            map_out = self.overlay
        else:
            map_out = self.board
        for i in map_out:
            for j in i:
                if j in markers:
                    buff_out.extend(colored(j, 'red'))
                elif j == GameState.FEATURES['fog']:
                    buff_out.extend(' ')
                elif j == GameState.FEATURES['water']:
                    buff_out.extend(colored(j, 'cyan', 'on_blue'))
                elif j == GameState.FEATURES['tree']:
                    buff_out.extend(colored(j, 'green', 'on_grey'))
                elif j == GameState.FEATURES['wall']:
                    buff_out.extend(colored(j, 'magenta', 'on_grey'))
                elif j == GameState.FEATURES['land']:
                    buff_out.extend(colored(' ', 'white', 'on_grey'))
                elif j == GameState.FEATURES['boat']:
                    buff_out.extend(colored(j, 'white', 'on_blue'))
                elif j == GameState.FEATURES['gold']:
                    buff_out.extend(colored(j, 'yellow', 'on_grey'))
                else:
                    buff_out.extend(j)
                buff_out.extend('')
            buff_out.extend('\n')
        print ''.join(buff_out)
        time.sleep(0.05)


    def directionAdjacent(self, current_location, adjacent):
        # given two coordinates, return direction
        if self.getUp(current_location) == adjacent:
            return GameState.CARDINAL['north']
        elif self.getLeft(current_location) == adjacent:
            return GameState.CARDINAL['west']
        elif self.getDown(current_location) == adjacent:
            return GameState.CARDINAL['south']
        elif self.getRight(current_location) == adjacent:
            return GameState.CARDINAL['east']


class Agent(object):
    'Agent class for agent of Bounty Game'

    INIT_ROTATION = 0  #change this
    LOG_ENABLED = True

    def __init__(self):
        self.state = GameState()
        self.location = self.state.board.START_LOCATION  # start in the middle of the allocated 2D list
        self.origin = self.location
        self.rotation = Agent.INIT_ROTATION  # {0, 1, 2, 3}
        self.is_in_boat = False
        self.num_dynamite = 0
        self.has_axe = False
        self.has_gold = False

        self.dumbCounter = 0

        # clear log file
        self.agentLog('\n--------\n')



    ### getters
    def isInBoat(self):
        return self.is_in_boat


    def getNumDynamite(self):
        return self.num_dynamite


    def getHasAxe(self):
        return self.has_axe


    def getHasGold(self):
        return self.has_gold


    ### setters
    # Pass in True or False to set the value of isInBoat
    def setInBoat(self, value):
        self.is_in_boat = value


    def setHasAxe(self):
        self.has_axe = True


    def setHasGold(self):
        self.has_gold = True


    def setGoldLocation(self, location):
        self.state.directory['gold'] = location


    def gainDynamite(self):
        self.num_dynamite += 1


    def expendDynamite(self):
        self.num_dynamite -= 1


    # returns space in front of player
    def _getFacing(self):
        if (self.rotation == GameState.CARDINAL['north']):
            target = self.state.board.getUp(self.location)
        elif (self.rotation == GameState.CARDINAL['east']):
            target = self.state.board.getRight(self.location)
        elif (self.rotation == GameState.CARDINAL['south']):
            target = self.state.board.getDown(self.location)
        else: #(self.rotation == GameState.CARDINAL['west'])
            target = self.state.board.getLeft(self.location)
        return target


    def isFacingDynamite(self):
        return self.state.board.isDynamite(self._getFacing())


    def isFacingTree(self):
        return self.state.board.isTree(self._getFacing())


    def isFacingBoat(self):
        return self.state.board.isBoat(self._getFacing())


    def isFacingWater(self):
        return self.state.board.isWater(self._getFacing())


    def isFacingWall(self):
        return self.state.board.isWall(self._getFacing())


    def isFacingAxe(self):
        return self.state.board.isAxe(self._getFacing())


    def isFacingGold(self):
        return self.state.board.isGold(self._getFacing())


    def isFacingLand(self):
        return self.state.board.isLand(self._getFacing())


    def isFacingEdge(self):
        return self.state.board.isEdge(self._getFacing())


    def canMoveForward(self):
        if self.isFacingLand():
            return True
        if self.isFacingAxe():
            return True
        if self.isFacingDynamite():
            return True
        if self.isFacingGold():
            return True
        if self.isFacingBoat():
            return True
        if self.isInBoat():
            if self.isFacingWater():
                return True
            if self.isFacingLand():
                return True
            if self.isFacingAxe():
                return True
            if self.isFacingGold():
                return True
        return False


    def canRemoveTree(self):
        # note: a tree can be chopped from inside boat - tested
        if self.isFacingTree() and self.getHasAxe():
            return True


    def canRemoveWall(self):
        # note: a wall can be blasted from inside boat - tested
        if self.isFacingWall() and self.getNumDynamite():
            return True


    ### setters
    def moveForward(self):
        if self.canMoveForward():
            # update inventory if necessary, if we are facing and have moved forward, then we obtain
            if self.isFacingAxe():
                self.setHasAxe()
                self.state.setNoneAxeLocation()
            elif self.isFacingDynamite():
                self.state.removeDynamiteFromList(self._getFacing())
                self.gainDynamite()
            elif self.isFacingGold():
                self.setHasGold()
                self.state.setNoneGoldLocation()
            elif self.isFacingBoat():
                self.state.setNoneBoatLocation(self._getFacing())
                self.setInBoat(True)
            elif self.isInBoat() and self.isFacingLand():
                self.state.setBoatLocation(self.location)
                self.setInBoat(False)

            # note: GameState.sendMove() will update internal representation of the board
            # update agent location
            #self.location = self.state.board.getUp(self.location) #WRONG
            self.location = self._getFacing()
            self.state.sendMove(GameState.MOVES['forward'], self.location, self.rotation)


    def moveUp(self):
        while self.rotation != GameState.CARDINAL['north']:
            if self.rotation == GameState.CARDINAL['west']:
                self.turnRight()
            else:
                self.turnLeft()
        self.moveForward()


    def moveRight(self):
        while self.rotation != GameState.CARDINAL['east']:
            if self.rotation == GameState.CARDINAL['north']:
                self.turnRight()
            else:
                self.turnLeft()
        if self.canMoveForward():
            self.moveForward()


    def moveDown(self):
        while self.rotation != GameState.CARDINAL['south']:
            if self.rotation == GameState.CARDINAL['east']:
                self.turnRight()
            else:
                self.turnLeft()
        if self.canMoveForward():
            self.moveForward()


    def moveLeft(self):
        while self.rotation != GameState.CARDINAL['west']:
            if self.rotation == GameState.CARDINAL['south']:
                self.turnRight()
            else:
                self.turnLeft()
        if self.canMoveForward():
            self.moveForward()


    def followDirection(self, direction):
        if direction == GameState.CARDINAL['north']:
            self.moveUp()
        elif direction == GameState.CARDINAL['east']:
            self.moveRight()
        elif direction == GameState.CARDINAL['south']:
            self.moveDown()
        elif direction == GameState.CARDINAL['west']:
            self.moveLeft()


    def followPath(self, path):
        for direction in path:
            self.followDirection(direction)


    def removeTree(self):
        if self.canRemoveTree():
            self.state.removeTreeFromList(self._getFacing())
            self.state.sendMove(GameState.MOVES['chop'], self.location, self.rotation)


    def removeWall(self):
        if self.canRemoveWall():
            self.state.sendMove(GameState.MOVES['blast'], self.location, self.rotation)
            self.expendDynamite()


    def turnLeft(self):
        self.rotation += GameState.DIRECTIONS['left']
        self.rotation %= len(GameState.CARDINAL)
        self.state.sendMove(GameState.MOVES['left'], self.location, self.rotation)


    def turnRight(self):
        self.rotation += GameState.DIRECTIONS['right']
        self.rotation %= len(GameState.CARDINAL)
        self.state.sendMove(GameState.MOVES['right'], self.location, self.rotation)


    # location is a tuple of form (x, y)
    def getBoardLocation(self, location):
        return self.state.board.getLocation(location)

    # write in function that clears agentlog at start of program
    def agentLog(self, string):
        if Agent.LOG_ENABLED:
            with open('agent.log', 'a+') as agentlog:
                agentlog = open('agent.log', 'a+')
                agentlog.write(str(string)+"\n")



