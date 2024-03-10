# region imports
#Chat.GPT was used to help reach this result
from scipy.optimize import fsolve
import numpy as np
# endregion

# region class definitions
# Import all classes from HW6_1_OOP.py
from HW6_1_OOP import ResistorNetwork, Resistor, VoltageSource, Loop

class ResistorNetwork2(ResistorNetwork):
    # Additional modifications if needed

    def AnalyzeCircuit(self):
        """
        Override the AnalyzeCircuit function to handle the second circuit.
        :return: a list of the currents in the resistor network
        """
        # Need to set the currents so that Kirchhoff's laws are satisfied
        # Use approximate values based on your analysis as the initial guess
        i0 = [2.0, 6.0, 8.0, 0.0]  # Add an initial guess for the new current
        i = fsolve(self.GetKirchoffVals, i0)

        # Print output to the screen
        print("I1 = {:0.1f}".format(i[0]))
        print("I2 = {:0.1f}".format(i[1]))
        print("I3 = {:0.1f}".format(i[2]))
        print("I4 = {:0.1f}".format(i[3]))  # Print the new current

        return i

    def GetKirchoffVals(self, i):
        """
        Override the GetKirchoffVals function to handle the second circuit.
        :param i: a list of currents relevant to the circuit
        :return: a 1D array of loop voltage drops and node currents
        """
        # Set current in resistors in the top loop.
        self.GetResistorByName('ad').Current = i[0]  # I_1 in the diagram
        self.GetResistorByName('bc').Current = i[0]  # I_1 in the diagram
        self.GetResistorByName('cd').Current = i[2]  # I_3 in the diagram
        # Set current in resistor in the bottom loop.
        self.GetResistorByName('ce').Current = i[1]  # I_2 in the diagram

        # Set current in the new resistor
        self.GetResistorByName('df').Current = i[3]  # I_4 in the diagram

        # Calculate net current into node c
        Node_c_Current = sum([i[0], i[1], -i[2], -i[3]])

        KVL = self.GetLoopVoltageDrops()  # Two equations here
        KVL.append(Node_c_Current)  # One equation here

        result = np.zeros(len(KVL) + 1)  # Initialize result array with an additional element

        print("Length of KVL:", len(KVL))
        print("Length of result array:", len(result))

        try:
            for idx, kvl_val in enumerate(KVL):
                result[idx] = kvl_val
        except IndexError as e:
            print("IndexError: {}".format(e))
            print("KVL: {}".format(KVL))

        print("Shape of result array:", result.shape)

        return result  # Convert the result to a 1D array

# endregion

# region function calls
def main():
    """
    This program solves for the unknown currents in the modified circuit.
    :return: nothing
    """
    Net = ResistorNetwork2()  # Use the new ResistorNetwork2 class
    Net.BuildNetworkFromFile("ResistorNetwork_2.txt")  # Call the function from Net that builds the resistor network from a text file
    IVals = Net.AnalyzeCircuit()

# endregion

# region function calls
if __name__ == "__main__":
    main()
# endregion

