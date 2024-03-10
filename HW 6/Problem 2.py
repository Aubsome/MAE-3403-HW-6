# region imports
import numpy as np
import math
from scipy.optimize import fsolve
import random as rnd
from Problem_1_Test_2 import *
# endregion

# region class definitions

class ResistorNetwork2(ResistorNetwork):
    def __init__(self):
        # Call the constructor of the base class
        super().__init__()

    # Override the necessary methods for the second circuit
    def AnalyzeCircuit(self):
        """
        Use fsolve to find currents in the resistor network for the modified circuit.
        1. KCL:  The total current flowing into any node in the network is zero.
        2. KVL:  When traversing a closed loop in the circuit, the net voltage drop must be zero.
        :return: a list of the currents in the resistor network
        """
        # need to set the currents so that Kirchhoff's laws are satisfied
        i0 = [0.0] * len(self.Resistors)  # define an initial guess for the currents in the circuit
        i = fsolve(self.GetKirchoffVals, i0)
        # print output to the screen
        for idx, current in enumerate(i):
            print("I{} = {:0.1f}".format(idx + 1, current))
        return i

    def GetKirchoffVals(self, i):
        print("Input i:", i)
        """
        This function uses Kirchhoff Voltage and Current laws to analyze this specific circuit
        KVL:  The net voltage drop for a closed loop in a circuit should be zero
        KCL:  The net current flow into a node in a circuit should be zero
        :param i: a list of currents relevant to the circuit
        :return: a list of loop voltage drops and node currents
        """
        # set current in resistors in the top loop.
        self.GetResistorByName('ad').Current = i[0]  # I_1 in the diagram
        self.GetResistorByName('bc').Current = i[0]  # I_1 in the diagram
        self.GetResistorByName('parallel_resistor').Current = i[4]  # Current through the parallel resistor
        # set current in resistor in the bottom loop.
        self.GetResistorByName('ce').Current = i[1]  # I_2 in the diagram
        # calculate net current into node c
        Node_c_Current = sum([i[0], i[1], -i[2]])

        KVL = self.GetLoopVoltageDrops()  # two equations here
        KVL.append(Node_c_Current)  # one equation here
        print("Output KVL:", KVL)
        print("Node_c_Current:", Node_c_Current)
        return np.zeros_like(i)  # Ensure the output is a 1D array

class Fluid():
    # region constructor
    def __init__(self, mu=0.00089, rho=1000):
        '''
        Initializes a Fluid object with default properties for water.

        :param mu: Dynamic viscosity in Pa*s -> (kg*m/s^2)*(s/m^2) -> kg/(m*s)
        :param rho: Density in kg/m^3
        '''
        self.mu = mu
        self.rho = rho
        self.nu = mu / rho
    # endregion

class Node():
    # region constructor
    def __init__(self, Name='a', Pipes=[], ExtFlow=0):
        '''
        Initializes a Node object in a pipe network.

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
        External flow and flow rates from connected pipes are considered.

        :return: Net flow rate into the node
        '''
        Qtot = self.extFlow
        for p in self.pipes:
            Qtot += p.getFlowIntoNode(self.name)
        return Qtot
    # endregion

class Loop():
    # region constructor
    def __init__(self, Name='A', Pipes=[]):
        '''
        Initializes a Loop object in a pipe network.

        :param Name: Name of the loop
        :param Pipes: A list of pipes in this loop
        '''
        self.name = Name
        self.pipes = Pipes
    # endregion

    # region methods/functions
    def getLoopHeadLoss(self):
        '''
        Calculates the net head loss as traversing around the loop in m of fluid.

        :return: Net head loss around the loop
        '''
        deltaP = 0
        startNode = self.pipes[0].startNode
        for p in self.pipes:
            phl = p.getFlowHeadLoss(startNode)
            deltaP += phl
            startNode = p.endNode if startNode != p.endNode else p.startNode
        return deltaP
    # endregion

class Pipe():
    # region constructor
    def __init__(self, Start='A', End='B', L=100, D=200, r=0.00025, fluid=Fluid()):
        '''
        Initializes a Pipe object with orientation from lowest letter to highest, alphabetically.

        :param Start: The start node (string)
        :param End: The end node (string)
        :param L: The pipe length in m (float)
        :param D: The pipe diameter in mm (float)
        :param r: The pipe roughness in m  (float)
        :param fluid: A Fluid object (typically water)
        '''
        self.startNode = min(Start, End)
        self.endNode = max(Start, End)
        self.length = L
        self.r = r
        self.fluid = fluid

        self.d = D / 1000.0
        self.relrough = self.r / self.d
        self.A = math.pi / 4.0 * self.d ** 2
        self.Q = 10
        self.vel = self.V()
        self.reynolds = self.Re()
    # endregion

    # region methods/functions
    def V(self):
        '''
        Calculates average velocity in the pipe for volumetric flow self.Q.

        :return: The average velocity in m/s
        '''
        self.vel = self.Q / self.A
        return self.vel

    def Re(self):
        '''
        Calculates the Reynolds number under current conditions.

        :return: The Reynolds number
        '''
        self.reynolds = self.fluid.rho * self.V() * self.d / self.fluid.mu
        return self.reynolds

    def FrictionFactor(self):
        """
        Calculates the friction factor for a pipe based on the notion of laminar, turbulent, and transitional flow.

        :return: The (Darcy) friction factor
        """
        Re = self.Re()
        rr = self.relrough

        def CB(f):
            cb = 1 / (f ** 0.5) + 2.0 * np.log10(rr / 3.7 + 2.51 / (Re * f ** 0.5))
            return cb

        def lam():
            return 64 / Re

        if Re >= 4000:
            return fsolve(CB, 0.01)[0]
        if Re <= 2000:
            return lam()

        CBff = fsolve(CB, 0.01)[0]
        Lamff = lam()
        mean = Lamff + ((Re - 2000) / (4000 - 2000)) * (CBff - Lamff)
        sig = 0.2 * mean
        return rnd.normalvariate(mean, sig)

    def frictionHeadLoss(self):
        '''
        Uses the Darcy-Weisbach equation to find the head loss through a section of pipe.

        :return: The head loss in m of water
        '''
        g = 9.81
        ff = self.FrictionFactor()
        hl = 4 * ff * self.length * self.V() ** 2 / (2 * g * self.d)
        return hl

    def getFlowHeadLoss(self, s):
        '''
        Calculates the head loss for the pipe.

        :param s: The node I'm starting with in a traversal of the pipe
        :return: The signed head loss through the pipe in m of fluid
        '''
        nTraverse = 1 if s == self.startNode else -1
        nFlow = 1 if self.Q >= 0 else -1
        return nTraverse * nFlow * self.frictionHeadLoss()

    def Name(self):
        '''
        Gets the pipe name.

        :return: The pipe name
        '''
        return f"{self.startNode}-{self.endNode}"

    def oContainsNode(self, node):
        '''
        Determines if the pipe connects to the node.

        :param node: A node object
        :return: True if the pipe connects to the node, False otherwise
        '''
        return self.startNode == node or self.endNode == node

    def printPipeFlowRate(self):
        '''
        Prints the flow rate in the pipe.

        :return: None
        '''
        print(f'The flow in segment {self.Name()} is {self.Q:.2f} L/s')

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
        Initializes a PipeNetwork object containing pipe, node, loop, and fluid objects.

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
        Analyzes the pipe network and finds the flow rates in each pipe using fsolve.

        :return: A list of flow rates in the pipes
        '''
        N = len(self.nodes) + len(self.loops)
        Q0 = np.full(N, 10)

        def fn(q):
            """
            A callback for fsolve to find the roots of mass continuity equations at nodes
            and pressure drop equations in loops.

            :param q: An array of flow rates in the pipes + 1 extra value b/c of node b
            :return: An array containing flow rates at the nodes and pressure losses for the loops
            """
            for i in range(len(self.pipes)):
                self.pipes[i].Q = q[i]
            L = self.getNodeFlowRates()
            L += self.getLoopHeadLosses()
            return L

        FR = fsolve(fn, Q0)
        return FR

    def getNodeFlowRates(self):
        '''
        Calculates the net flow rates for each node in the pipe network.

        :return: A list of net flow rates for each node
        '''
        qNet = [n.getNetFlowRate() for n in self.nodes]
        return qNet

    def getLoopHeadLosses(self):
        '''
        Calculates the net head losses for each loop in the pipe network.

        :return: A list of net head losses for each loop
        '''
        lhl = [l.getLoopHeadLoss() for l in self.loops]
        return lhl

    def getPipe(self, name):
        '''
        Returns a pipe object by its name.

        :param name: The name of the pipe
        :return: The pipe object
        '''
        for p in self.pipes:
            if name == p.Name():
                return p

    def getNodePipes(self, node):
        '''
        Returns a list of pipe objects that are connected to the node object.

        :param node: A node object
        :return: A list of pipe objects connected to the node
        '''
        l = []
        for p in self.pipes:
            if p.oContainsNode(node):
                l.append(p)
        return l

    def nodeBuilt(self, node):
        '''
        Determines if a node object has already been constructed.

        :param node: A node object
        :return: True if the node has been constructed, False otherwise
        '''
        for n in self.nodes:
            if n.name == node:
                return True
        return False

    def getNode(self, name):
        '''
        Returns a node object by its name.

        :param name: The name of the node
        :return: The node object
        '''
        for n in self.nodes:
            if n.name == name:
                return n

    def buildNodes(self):
        '''
        Automatically creates the node objects by looking at the pipe ends.

        :return: None
        '''
        for p in self.pipes:
            if not self.nodeBuilt(p.startNode):
                self.nodes.append(Node(p.startNode, self.getNodePipes(p.startNode)))
            if not self.nodeBuilt(p.endNode):
                self.nodes.append(Node(p.endNode, self.getNodePipes(p.endNode)))

    def printPipeFlowRates(self):
        '''
        Prints the flow rates in each pipe.

        :return: None
        '''
        for p in self.pipes:
            p.printPipeFlowRate()

    def printNetNodeFlows(self):
        '''
        Prints the net flow rates into each node.

        :return: None
        '''
        for n in self.nodes:
            print(f'Net flow into node {n.name} is {n.getNetFlowRate():.2f}')

    def printLoopHeadLoss(self):
        '''
        Prints the head losses for each loop.

        :return: None
        '''
        for l in self.loops:
            print(f'Head loss for loop {l.name} is {l.getLoopHeadLoss():.2f}')

    # endregion

# endregion

# region function definitions
def main():
    '''
    This program analyzes flows in a given pipe network based on the following:
    1. The pipe segments are named by their endpoint node names: e.g., a-b, b-e, etc.
    2. Flow from the lower letter to the higher letter of a pipe is considered positive.
    3. Pressure decreases in the direction of flow through a pipe.
    4. At each node in the pipe network, mass is conserved.
    5. For any loop in the pipe network, the pressure loss is zero.

    Approach to analyzing the pipe network:
    Step 1: Build a pipe network object that contains pipe, node, loop, and fluid objects
    Step 2: Calculate the flow rates in each pipe using fsolve
    Step 3: Output results
    Step 4: Check results against expected properties of zero head loss around a loop and mass conservation at nodes.

    :return: None
    '''
    # Instantiate a Fluid object to define the working fluid as water
    water = Fluid()

    # Roughness in meters
    roughness = 0.00025

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
    PN.loops.append(Loop('A', [PN.getPipe('a-b'), PN.getPipe('b-e'), PN.getPipe('d-e'), PN.getPipe('c-d'), PN.getPipe('a-c')]))
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
