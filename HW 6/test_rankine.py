#Chat.GPT was used to help reach this result
# test_rankine.py

from rankine import rankine

def main():
    """
    Main function to test Rankine cycles with different parameters and print the results.
    """
    # Test Case 1
    rankine_case1 = rankine(p_high=8000, p_low=8, name='Rankine Cycle Case 1')
    efficiency_case1 = rankine_case1.calc_efficiency()
    rankine_case1.print_summary()
    print(f'Efficiency: {efficiency_case1:.3f}%\n')

    # Test Case 2
    rankine_case2 = rankine(p_high=8000, p_low=8, t_high=1.7, name='Rankine Cycle Case 2')
    efficiency_case2 = rankine_case2.calc_efficiency()
    rankine_case2.print_summary()
    print(f'Efficiency: {efficiency_case2:.3f}%')

# Execute the main function if this script is run
if __name__ == "__main__":
    main()
