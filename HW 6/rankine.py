#Chat.GPT was used to help reach this result
# rankine.py

from Steam import steam

class rankine:
    """
    Rankine class represents a Rankine power cycle and provides methods to calculate cycle properties and print summaries.
    """
    def __init__(self, p_low=8, p_high=8000, t_high=None, name='Rankine Cycle'):
        """
        Constructor for Rankine power cycle.

        :param p_low: the low pressure isobar for the cycle in kPa
        :param p_high: the high pressure isobar for the cycle in kPa
        :param t_high: optional temperature for State1 (turbine inlet) in degrees C
        :param name: a convenient name
        """
        self.p_low = p_low
        self.p_high = p_high
        self.t_high = t_high
        self.name = name
        self.efficiency = None
        self.turbine_work = 0
        self.pump_work = 0
        self.heat_added = 0
        self.state1 = None
        self.state2 = None
        self.state3 = None
        self.state4 = None

    def calc_efficiency(self):
        """
        Calculate the efficiency and other properties of the Rankine cycle.

        :return: efficiency of the Rankine cycle
        """
        # Calculate the 4 states
        # state 1: turbine inlet (p_high, t_high) superheated or saturated vapor
        if self.t_high is None:
            self.state1 = steam(self.p_high, name='Turbine Inlet')  # instantiate a steam object with conditions of state 1 as saturated steam
        else:
            self.state1 = steam(self.p_high, T=self.t_high, name='Turbine Inlet')  # instantiate a steam object with conditions of state 1 at t_high

        # state 2: turbine exit (p_low, s=s_turbine inlet) two-phase
        self.state2 = steam(self.p_low, s=self.state1.s, name='Turbine Exit')

        # state 3: pump inlet (p_low, x=0) saturated liquid
        self.state3 = steam(self.p_low, x=0, name='Pump Inlet')

        # state 4: pump exit (p_high, s=s_pump_inlet) typically sub-cooled, but estimate as saturated liquid
        self.state4 = steam(self.p_high, s=self.state3.s, name='Pump Exit')
        self.state4.h = self.state3.h + self.state3.v * (self.p_high - self.p_low)

        self.turbine_work = self.state1.h - self.state2.h  # calculate turbine work
        self.pump_work = self.state4.h - self.state3.h  # calculate pump work
        self.heat_added = self.state1.h - self.state4.h  # calculate heat added
        self.efficiency = 100.0 * (self.turbine_work - self.pump_work) / self.heat_added

        # Return the calculated efficiency
        return self.efficiency

    def print_summary(self):
        """
        Print a summary of the Rankine cycle properties.

        :return: None
        """
        if self.efficiency is None:
            self.calc_efficiency()
        print('Cycle Summary for: ', self.name)
        print('\tEfficiency: {:0.3f}%'.format(self.efficiency))
        print('\tTurbine Work: {:0.3f} kJ/kg'.format(self.turbine_work))
        print('\tPump Work: {:0.3f} kJ/kg'.format(self.pump_work))
        print('\tHeat Added: {:0.3f} kJ/kg'.format(self.heat_added))
        self.state1.print()
        self.state2.print()
        self.state3.print()
        self.state4.print()

def main():
    """
    Main function to test the Rankine cycle.

    :return: None
    """
    rankine1 = rankine(p_high=8000, p_low=8, name='Rankine Cycle Test')
    eff = rankine1.calc_efficiency()
    print(eff)
    rankine1.print_summary()

if __name__ == "__main__":
    main()
