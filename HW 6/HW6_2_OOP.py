# region imports
import numpy as np
import math
from scipy.optimize import fsolve
import random as rnd
# endregion

# region class definitions
class Fluid():
    # region constructor
    def __init__(self, mu=0.00089, rho=1000):
        '''
        Default properties are for water.
        :param mu: Dynamic viscosity in Pa*s -> (kg*m/s^2)*(s/m^2) -> kg/(m*s)
        :param rho: Density in kg/m^3
        '''
        self.mu = mu  # Copy the value in the argument as a class property
        self.rho = rho  # Copy the value in the argument as a class property
        self.nu = mu / rho  # Calculate the kinematic viscosity in units of m^2/s
    # endregion


class Node():
    # region constructor
    def __init__(self, Name='a', Pipes=[], ExtFlow=0):
        '''
        A node in a pipe network.
        :param Name: Name of the node
        :param Pipes: A list of pipes connected to this node
        :param ExtFlow: Any external flow into (+) or out (-) of this node in L/s
        '''
        self.name = Name
        self.pipes = Pipes
        self.extFlow = ExtFlow

    # endregion

    # region methods/functions
    def getNetFlowRate(self):
        '''
        Calculates the net flow rate into this node in L/s.
        :return: Net flow rate into the node
        '''
        Qtot = self.extFlow  # Count the external flow first
        for p in self.pipes:
            # Retrieves the pipe flow rate (+) if into node (-) if out of node.
            # See class for the pipe.
            Qtot += p.getFlowIntoNode(self.name)
        return Qtot
    # endregion


class Loop():
    # region constructor
    def __init__(self, Name='A', Pipes=[]):
        '''
        Defines a loop in a pipe network.
        Note: The pipes must be listed in order. The traversal of a pipe loop
        will begin at the start node of Pipe[0] and move in the positive direction of that pipe.
        Hence, loops can be either CW or CCW traversed, depending on which pipe you start with.
        Should work fine either way.
        :param Name: Name of the loop
        :param Pipes: A list/array of pipes in this loop
        '''
        self.name = Name
        self.pipes = Pipes
    # endregion

    # region methods/functions
    def getLoopHeadLoss(self):
        """
        Calculates the net head loss as I traverse around the loop, in m of fluid.
        """
        deltaP = 0  # initialize to zero
        startNode = self.pipes[0].startNode  # begin at the start node of the first pipe
        for p in self.pipes:
            # calculates the head loss in the pipe considering loop traversal and flow directions
            phl = p.getFlowHeadLoss(startNode)
            deltaP += phl
            startNode = p.endNode if startNode != p.endNode else p.startNode  # move to the next node
        return abs(deltaP)
    # endregion


class Pipe():
    # region constructor
    def __init__(self, Start='A', End='B', L=100, D=200, r=0.00025, fluid=Fluid()):
        '''
        Defines a generic pipe with orientation from lowest letter to highest, alphabetically.
        :param Start: The start node (string)
        :param End: The end node (string)
        :param L: The pipe length in m (float)
        :param D: The pipe diameter in mm (float)
        :param r: The pipe roughness in m  (float)
        :param fluid: A Fluid object (typically water)
        '''
        # From arguments given in constructor
        self.startNode = min(Start, End)  # Makes sure to use the lowest letter for startNode
        self.endNode = max(Start, End)  # Makes sure to use the highest letter for the endNode
        self.length = L
        self.r = r
        self.fluid = fluid  # The fluid in the pipe

        # Other calculated properties
        self.d = D / 1000.0  # Diameter in m
        self.relrough = self.r / self.d  # Calculate relative roughness for easy use later
        self.A = math.pi / 4.0 * self.d ** 2  # Calculate pipe cross-sectional area for easy use later
        self.Q = 10  # Working in units of L/s, just an initial guess
        self.vel = self.V()  # Calculate the initial velocity of the fluid
        self.reynolds = self.Re()  # Calculate the initial Reynolds number
    # endregion

    # region methods/functions
    def V(self):
        '''
        Calculate average velocity in the pipe for volumetric flow self.Q.
        :return: The average velocity in m/s
        '''
        self.vel = self.Q / self.A  # The average velocity is Q/A (be mindful of units)
        return self.vel

    def Re(self):
        '''
        Calculate the Reynolds number under current conditions.
        :return: The Reynolds number
        '''
        self.reynolds = self.fluid.rho * self.vel * self.d / self.fluid.mu
        return self.reynolds

    def FrictionFactor(self):
        """
        This function calculates the friction factor for a pipe based on the
        notion of laminar, turbulent, and transitional flow.
        :return: The (Darcy) friction factor
        """
        # Update the Reynolds number and make a local variable Re
        Re = self.Re()
        rr = self.relrough

        # To be used for turbulent flow
        def CB():
            # Note: In numpy, log is for natural log. log10 is log base 10.
            cb = lambda f: 1 / (f ** 0.5) + 2.0 * np.log10(rr / 3.7 + 2.51 / (Re * f ** 0.5))
            result = fsolve(cb, (0.01))
            val = cb(result[0])
            return result[0]

        # To be used for laminar flow
        def lam():
            return 64 / Re

        if Re >= 4000:  # True for turbulent flow
            return CB()
        if Re <= 2000:  # True for laminar flow
            return lam()

        # Transition flow is ambiguous, so use normal variate weighted by Re
        CBff = CB()
        Lamff = lam()

        # I assume laminar is more accurate when just above 2000 and CB more accurate when just below Re 4000.
        # I will weight the mean appropriately using linear interpolation.
        mean = Lamff + ((Re - 2000) / (4000 - 2000)) * (CBff - Lamff)
        sig = 0.2 * mean

        # Now, use normalvariate to put some randomness in the choice
        return rnd.normalvariate(mean, sig)

    def frictionHeadLoss(self):
        """
        Use the Darcy-Weisbach equation to find the head loss through a section of pipe.
        """
        g = 9.81  # m/s^2
        ff = self.FrictionFactor()
        # Calculate the head loss in m of water
        hl = (ff * self.length * (self.vel ** 2)) / (2 * g * self.d)
        return hl

    def getFlowHeadLoss(self, s):
        '''
        Calculate the head loss for the pipe.
        :param s: The node I'm starting with in a traversal of the pipe
        :return: The signed head loss through the pipe in m of fluid
        '''
        # While traversing a loop, if s = startNode I'm traversing in the same direction as the positive pipe
        nTraverse = 1 if s == self.startNode else -1
        # If flow is positive sense, scalar = 1 else = -1
        nFlow = 1 if self.Q >= 0 else -1
        return nTraverse * nFlow * self.frictionHeadLoss()

    def Name(self):
        '''
        Gets the pipe name.
        :return: The pipe name
        '''
        return self.startNode + '-' + self.endNode

    def oContainsNode(self, node):
        # Does the pipe connect to the node?
        return self.startNode == node or self.endNode == node

    def printPipeFlowRate(self):
        print('The flow in segment {} is {:0.2f} L/s'.format(self.Name(), self.Q))

    def getFlowIntoNode(self, n):
        '''
        Determines the flow rate into node n.
        :param n: A node object
        :return: +/-Q
        '''
        if n == self.startNode:
            return -self.Q
        return self.Q
    # endregion


class PipeNetwork():
    # region constructor
    def __init__(self, Pipes=[], Loops=[], Nodes=[], fluid=Fluid()):
        '''
        The pipe network is built from pipe, node, loop, and fluid objects.
        :param Pipes: A list of pipe objects
        :param Loops: A list of loop objects
        :param Nodes: A list of node objects
        :param fluid: A fluid object
        '''
        self.loops = Loops
        self.nodes = Nodes
        self.Fluid = fluid
        self.pipes = Pipes
    # endregion

    # region methods/functions
    def findFlowRates(self):
        '''
        A method to analyze the pipe network and find the flow rates in each pipe
        given the constraints of: i) no net flow into a node and ii) no net pressure drops in the loops.
        :return: A list of flow rates in the pipes
        '''
        # See how many nodes and loops there are; this is how many equation results I will return
        N = len(self.nodes) + len(self.loops)
        # Build an initial guess for flow rates in the pipes
        Q0 = np.full(len(self.pipes), 10)

        def fn(q):
            """
            This is used as a callback for fsolve.
            The mass continuity equations at the nodes and the loop equations
            are functions of the flow rates in the pipes.
            Hence, fsolve will search for the roots of these equations
            by varying the flow rates in each pipe.
            :param q: An array of flow rates in the pipes
            :return: An array containing net flow rates at the nodes and head losses for the loops
            """
            # Update the flow rate in each pipe object
            for i in range(len(self.pipes)):
                self.pipes[i].Q = q[i]  # Set volumetric flow rate from input argument q

            # Calculate the net flow rate for the node objects
            # Note: When flow rates in pipes are correct, the net flow into each node should be zero.
            node_flow_rates = self.getNodeFlowRates()

            # Calculate the net head loss for the loop objects
            # Note: When the flow rates in pipes are correct, the net head loss for each loop should be zero.
            loop_head_losses = self.getLoopHeadLosses()

            # Combine the results into a single array
            result = np.concatenate((node_flow_rates, loop_head_losses))

            return result

    def getNodeFlowRates(self):
        # Each node object is responsible for calculating its own net flow rate
        qNet = [n.getNetFlowRate() for n in self.nodes]
        return qNet

    def getLoopHeadLosses(self):
        # Each loop object is responsible for calculating its own net head loss
        lhl = [l.getLoopHeadLoss() for l in self.loops]
        return lhl

    def getPipe(self, name):
        # Returns a pipe object by its name
        for p in self.pipes:
            if name == p.Name():
                return p

    def getNodePipes(self, node):
        # Returns a list of pipe objects that are connected to the node object
        l = []
        for p in self.pipes:
            if p.oContainsNode(node):
                l.append(p)
        return l

    def nodeBuilt(self, node):
        # Determines if I have already constructed this node object (by name)
        for n in self.nodes:
            if n.name == node:
                return True
        return False

    def getNode(self, name):
        # Returns one of the node objects by name
        for n in self.nodes:
            if n.name == name:
                return n

    def buildNodes(self):
        # Automatically create the node objects by looking at the pipe ends
        for p in self.pipes:
            if not self.nodeBuilt(p.startNode):
                # Instantiate a node object and append it to the list of nodes
                self.nodes.append(Node(p.startNode, self.getNodePipes(p.startNode)))
            if not self.nodeBuilt(p.endNode):
                # Instantiate a node object and append it to the list of nodes
                self.nodes.append(Node(p.endNode, self.getNodePipes(p.endNode)))

    def printPipeFlowRates(self):
        for p in self.pipes:
            p.printPipeFlowRate()

    def printNetNodeFlows(self):
        for n in self.nodes:
            print('Net flow into node {} is {:0.2f}'.format(n.name, n.getNetFlowRate()))

    def printLoopHeadLoss(self):
        for l in self.loops:
            print('Head loss for loop {} is {:0.2f}'.format(l.name, l.getLoopHeadLoss()))
    # endregion


# endregion

# region function definitions
def main():
    '''
    This program analyzes flows in a given pipe network based on the following:
    1. The pipe segments are named by their endpoint node names:  e.g., a-b, b-e, etc.
    2. Flow from the lower letter to the higher letter of a pipe is considered positive.
    3. Pressure decreases in the direction of flow through a pipe.
    4. At each node in the pipe network, mass is conserved.
    5. For any loop in the pipe network, the pressure loss is zero
    Approach to analyzing the pipe network:
    Step 1: build a pipe network object that contains pipe, node, loop, and fluid objects
    Step 2: calculate the flow rates in each pipe using fsolve
    Step 3: output results
    Step 4: check results against expected properties of zero head loss around a loop and mass conservation at nodes.
    :return:
    '''
    # Instantiate a Fluid object to define the working fluid as water
    water = Fluid()
    roughness = 0.00025  # in meters

    # Instantiate a new PipeNetwork object
    PN = PipeNetwork()
    # Add Pipe objects to the pipe network (see constructor for Pipe class)
    PN.pipes.append(Pipe('a', 'b', 250, 300, roughness, water))
    PN.pipes.append(Pipe('a', 'c', 100, 200, roughness, water))
    PN.pipes.append(Pipe('b', 'e', 100, 200, roughness, water))
    PN.pipes.append(Pipe('c', 'd', 125, 200, roughness, water))
    PN.pipes.append(Pipe('c', 'f', 100, 150, roughness, water))
    PN.pipes.append(Pipe('d', 'e', 125, 200, roughness, water))
    PN.pipes.append(Pipe('d', 'g', 100, 150, roughness, water))
    PN.pipes.append(Pipe('e', 'h', 100, 150, roughness, water))
    PN.pipes.append(Pipe('f', 'g', 125, 250, roughness, water))
    PN.pipes.append(Pipe('g', 'h', 125, 250, roughness, water))
    # Add Node objects to the pipe network by calling buildNodes method of PN object
    PN.buildNodes()

    # Update the external flow of certain nodes
    PN.getNode('a').extFlow = 60
    PN.getNode('d').extFlow = -30
    PN.getNode('f').extFlow = -15
    PN.getNode('h').extFlow = -15

    # Add Loop objects to the pipe network
    PN.loops.append(
        Loop('A', [PN.getPipe('a-b'), PN.getPipe('b-e'), PN.getPipe('d-e'), PN.getPipe('c-d'), PN.getPipe('a-c')]))
    PN.loops.append(Loop('B', [PN.getPipe('c-d'), PN.getPipe('d-g'), PN.getPipe('f-g'), PN.getPipe('c-f')]))
    PN.loops.append(Loop('C', [PN.getPipe('d-e'), PN.getPipe('e-h'), PN.getPipe('g-h'), PN.getPipe('d-g')]))

    # Call the findFlowRates method of the PN (a PipeNetwork object)
    PN.findFlowRates()

    # Get output
    PN.printPipeFlowRates()
    print()
    print('Check node flows:')
    PN.printNetNodeFlows()
    print()
    print('Check loop head loss:')
    PN.printLoopHeadLoss()


# endregion

# region function calls
if __name__ == "__main__":
    main()
# endregion
