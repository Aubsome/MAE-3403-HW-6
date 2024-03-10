# Imports
from scipy.optimize import fsolve
import numpy as np

# Class Definitions
class ResistorNetwork():
    """
    Represents a resistor network consisting of loops, resistors, and voltage sources.
    """
    # Constructor
    def __init__(self):
        """
        Initializes a resistor network with empty lists for loops, resistors, and voltage sources.
        """
        self.Loops = []        # Initialize an empty list of loop objects in the network
        self.Resistors = []     # Initialize an empty list of resistor objects in the network
        self.VSources = []      # Initialize an empty list of source objects in the network

    # Methods/Functions
    def BuildNetworkFromFile(self, filename):
        """
        Reads lines from a file and processes it to populate the fields for loops, resistors, and voltage sources.
        :param filename: String for the file to process.
        :return: Nothing
        """
        FileTxt = open(filename, "r").read().split('\n')
        LineNum = 0
        self.Resistors = []
        self.VSources = []
        self.Loops = []
        LineNum = 0
        lineTxt = ""
        FileLength = len(FileTxt)
        while LineNum < FileLength:
            lineTxt = FileTxt[LineNum].lower().strip()
            if len(lineTxt) < 1:
                pass  # Skip
            elif lineTxt[0] == '#':
                pass  # Skips comment lines
            elif "resistor" in lineTxt:
                LineNum = self.MakeResistor(LineNum, FileTxt)
            elif "source" in lineTxt:
                LineNum = self.MakeVSource(LineNum, FileTxt)
            elif "loop" in lineTxt:
                LineNum = self.MakeLoop(LineNum, FileTxt)
            LineNum += 1
        pass

    def MakeResistor(self, N, Txt):
        """
        Makes a resistor object from reading the text file.
        :param N: Line number for current processing.
        :param Txt: List of strings representing the lines of the text file.
        :return: Updated line number.
        """
        R = Resistor()
        N += 1
        if N < len(Txt):  # Check if N is within the valid range
            txt = Txt[N].lower()
        else:
            return N

        while N < len(Txt) and "resistor" not in txt:
            if "name" in txt:
                R.Name = txt.split('=')[1].strip()
            if "resistance" in txt:
                R.Resistance = float(txt.split('=')[1].strip())
            N += 1
            if N < len(Txt):  # Check if N is within the valid range
                txt = Txt[N].lower()

        self.Resistors.append(R)
        return N

    def MakeVSource(self, N, Txt):
        """
        Makes a voltage source object from reading the text file.
        :param N: Line number for current processing.
        :param Txt: List of strings representing the lines of the text file.
        :return: Updated line number.
        """
        VS = VoltageSource()
        N += 1
        txt = Txt[N].lower()
        while "source" not in txt:
            if "name" in txt:
                VS.Name = txt.split('=')[1].strip()
            if "value" in txt:
                VS.Voltage = float(txt.split('=')[1].strip())
            if "type" in txt:
                VS.Type = txt.split('=')[1].strip()
            N += 1
            txt = Txt[N].lower()

        self.VSources.append(VS)
        return N

    def MakeLoop(self, N, Txt):
        """
        Makes a Loop object from reading the text file.
        :param N: Line number for current processing.
        :param Txt: List of strings representing the lines of the text file.
        :return: Updated line number.
        """
        L = Loop()
        N += 1
        txt = Txt[N].lower()
        while "loop" not in txt:
            if "name" in txt:
                L.Name = txt.split('=')[1].strip()
            if "nodes" in txt:
                txt = txt.replace(" ", "")
                L.Nodes = txt.split('=')[1].strip().split(',')
            N += 1
            txt = Txt[N].lower()

        self.Loops.append(L)
        return N

    def AnalyzeCircuit(self):
        """
        Use fsolve to find currents in the resistor network.
        1. KCL:  The total current flowing into any node in the network is zero.
        2. KVL:  When traversing a closed loop in the circuit, the net voltage drop must be zero.
        :return: a list of the currents in the resistor network
        """
        # need to set the currents so that Kirchhoff's laws are satisfied
        # Adjust the length of i0 based on the number of unknown currents in your circuit
        i0 = np.zeros(5)  # Replace 5 with the correct number

        # Update the fsolve call to use an array of shape (1, 5) for the output
        i = fsolve(self.GetKirchoffVals, i0, full_output=1)

        # Extract the result from the output tuple
        i_result = i[0]

        # Print output to the screen
        for idx, current in enumerate(i_result):
            print("I{} = {:0.1f}".format(idx + 1, current))

        return i_result

    def GetKirchoffVals(self, i):
        """
        Uses Kirchhoff Voltage and Current laws to analyze this specific circuit.
        KVL: The net voltage drop for a closed loop in a circuit should be zero.
        KCL: The net current flow into a node in a circuit should be zero.
        :param i: A list of currents relevant to the circuit.
        :return: A 1D array of loop voltage drops and node currents.
        """
        print(f"Currents: {i}")  # Add this line for debugging

        # set current in resistors in the top loop.
        self.GetResistorByName('ad').Current = i[0]  # I_1 in diagram
        self.GetResistorByName('bc').Current = i[0]  # I_1 in diagram
        self.GetResistorByName('cd').Current = i[2]  # I_3 in diagram
        # set current in resistor in the bottom loop.
        self.GetResistorByName('ce').Current = i[1]  # I_2 in diagram
        # calculate net current into node c
        Node_c_Current = sum([i[0], i[1], -i[2]])
        print(f"Node c current: {Node_c_Current}")  # Add this line for debugging

        # Handle parallel resistor if necessary (uncomment the following lines when needed)
        # parallel_resistor = self.GetResistorByName('parallel')
        # parallel_resistor.Current = i[X]  # Replace X with the correct index based on your circuit

        KVL = self.GetLoopVoltageDrops()  # two equations here
        KVL.append(Node_c_Current)  # one equation here

        # Return a 1D array with the correct shape
        return np.array(KVL).flatten()

    def GetElementDeltaV(self, name):
        """
        Retrieves either a resistor or a voltage source by name.
        :param name: Name of the resistor or voltage source.
        :return: DeltaV for the element.
        """
        for r in self.Resistors:
            if name == r.Name:
                return -r.DeltaV()
            if name[::-1] == r.Name:
                return -r.DeltaV()
        for v in self.VSources:
            if name == v.Name:
                return v.Voltage
            if name[::-1] == v.Name:
                return v.Voltage

    def GetLoopVoltageDrops(self):
        """
        Calculates the net voltage drop around a closed loop in a circuit based on the
        current flowing through resistors (causing a drop in voltage regardless of the direction of traversal) or
        the value of the voltage source that has been set up as positive based on the direction of traversal.
        :return: Net voltage drop for all loops in the network.
        """
        loopVoltages = []
        for L in self.Loops:
            # Traverse loops in order of nodes and add up voltage drops between nodes
            loopDeltaV = 0
            for n in range(len(L.Nodes)):
                if n == len(L.Nodes) - 1:
                    name = L.Nodes[0] + L.Nodes[n]
                else:
                    name = L.Nodes[n] + L.Nodes[n + 1]
                loopDeltaV += self.GetElementDeltaV(name)
            loopVoltages.append(loopDeltaV)
        return loopVoltages

    def GetResistorByName(self, name):
        """
        Retrieves a resistor object from self.Resistors based on resistor name.
        :param name: Name of the resistor.
        :return: Resistor object.
        """
        for r in self.Resistors:
            if r.Name == name:
                return r


class Loop():
    """
    Represents a loop in the resistor network.
    """
    # Constructor
    def __init__(self):
        """
        Defines a loop as a list of node names.
        """
        self.Nodes = []


class Resistor():
    """
    Represents a resistor in the resistor network.
    """
    # Constructor
    def __init__(self, R=1.0, i=0.0, name='ab'):
        """
        Defines a resistor to have a self.Resistance, self.Current, and self.Name instance variables.
        :param R: Resistance in Ohm.
        :param i: Current in amps.
        :param name: Name of resistor by alphabetically ordered pair of node names.
        """
        self.Resistance = R
        self.Current = i
        self.Name = name

    # Methods/Functions
    def DeltaV(self):
        """
        Calculates voltage change across the resistor.
        :return: The signed value of voltage drop. Voltage drop > 0 in the direction of positive current flow.
        """
        return self.Current * self.Resistance


class VoltageSource():
    """
    Represents a voltage source in the resistor network.
    """
    # Constructor
    def __init__(self, V=12.0, name='ab'):
        """
        Defines a voltage source with instance variables of self.Voltage = V, self.Name = name.
        :param V: The voltage.
        :param name: The name of the voltage source. The voltage source naming convention is to use the nodes such as 'ab'
        where the order of the nodes goes in the direction of positive voltage change as I traverse the loop from a to b.
        """
        self.Voltage = V
        self.Name = name


# Function Definitions
def main():
    """
    Solves for the unknown currents in the circuit of the homework assignment.
    :return: Nothing
    """
    Net = ResistorNetwork()  # Instantiate a resistor network object
    Net.BuildNetworkFromFile("ResistorNetwork_2.txt")
    IVals = Net.AnalyzeCircuit()


# Function Calls
if __name__ == "__main__":
    main()
