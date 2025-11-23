import logging
import math # Import math for isnan check


# UNIT TESTING: Test year generation, correct application of rates, base year handling.
def generate_living_costs(base_cost, base_year, rate_pre_retirement, rate_post_retirement, retirement_year, final_year, one_off_expenses=None, slow_down_year=None, rate_post_slow_down=0.0):
    """
    Generates a dictionary of projected annual living costs based on provided rates and years,
    incorporating one-off expenses and a potential 'slow down' phase in later life.

    Args:
        base_cost (float): The living cost in the base_year.
        base_year (int): The year corresponding to the base_cost.
        rate_pre_retirement (float): Annual rate of living cost increase before retirement.
        rate_post_retirement (float): Annual rate of living cost increase after retirement (active phase).
        retirement_year (int): The year retirement occurs.
        final_year (int): The final year of the simulation.
        one_off_expenses (dict, optional): Dictionary mapping specific years to additional costs.
        slow_down_year (int, optional): Year when the 'slow down' phase begins (expenses change rate). 
                                        If None, post-retirement rate applies until end.
        rate_post_slow_down (float): Annual rate of living cost increase after the slow_down_year. 
                                     Defaults to 0.0 (flat real terms).

    Returns:
        dict: A dictionary where keys are years (int) and values are projected living costs (float).
    """
    r1 = 1 + rate_pre_retirement
    r2 = 1 + rate_post_retirement
    r3 = 1 + rate_post_slow_down

    start_year = base_year
    
    # 1. Pre-Retirement Phase
    d1 = {year: base_cost * (r1)**(year - start_year) for year in range(start_year, retirement_year + 1)}

    # 2. Post-Retirement Phase
    current_cost = d1.get(retirement_year, base_cost * (r1)**(retirement_year - base_year))
    
    # Determine effective end of active retirement phase
    if slow_down_year and slow_down_year > retirement_year:
        active_retirement_end = min(slow_down_year, final_year)
    else:
        active_retirement_end = final_year

    d2 = {}
    for year in range(retirement_year + 1, active_retirement_end + 1):
        current_cost *= r2
        d2[year] = current_cost

    # 3. Slow-Down Phase
    d3 = {}
    if slow_down_year and slow_down_year < final_year and slow_down_year >= retirement_year:
        # current_cost is now at slow_down_year level
        for year in range(active_retirement_end + 1, final_year + 1):
            current_cost *= r3
            d3[year] = current_cost

    # Combine all phases
    combined_costs = {**d1, **d2, **d3}

    # Add one-off expenses if provided
    if one_off_expenses:
        for year, amount in one_off_expenses.items():
            year_int = int(year)
            if year_int in combined_costs:
                combined_costs[year_int] += float(amount)
            elif start_year <= year_int <= final_year:
                 combined_costs[year_int] = float(amount)

    return combined_costs

# UNIT TESTING: Test year generation, correct application of rates, base year handling.
def generate_salary(base_salary, base_year, growth_rate, last_work_year, growth_stop_year=None, post_plateau_growth_rate=0.0):
    """
    Generates a dictionary of projected annual gross salaries based on a growth rate and final work year.
    Allows for a 'plateau' or decline where growth changes after a specific year.

    Args:
        base_salary (float): The gross salary in the base_year.
        base_year (int): The year corresponding to the base_salary.
        growth_rate (float): Annual salary growth rate until the stop year (e.g., 0.01 for 1%).
        last_work_year (int): The final year the salary is earned.
        growth_stop_year (int, optional): The year after which salary growth changes to the post-plateau rate. 
                                          If None, grows at initial rate until last_work_year.
        post_plateau_growth_rate (float): Annual salary growth rate AFTER the stop year (e.g., -0.01 for 1% decline).
                                          Defaults to 0.0 (flat plateau).

    Returns:
        dict: A dictionary where keys are years (int) and values are projected gross salaries (float).
    """
    r_initial = 1 + growth_rate
    r_post = 1 + post_plateau_growth_rate
    
    start_year = base_year # Use the provided base_year
    
    salaries = {}
    current_salary = base_salary
    
    # Determine the effective stop year for growth
    effective_growth_stop = growth_stop_year if growth_stop_year is not None else last_work_year

    # Iterate from start_year to last_work_year
    for year in range(start_year, last_work_year + 1):
        if year == start_year:
             salaries[year] = base_salary
        else:
             # If the *previous* year was before the stop year, we grow at initial rate.
             if (year - 1) < effective_growth_stop:
                 current_salary *= r_initial
             # Else we grow (or shrink) at the post-plateau rate
             else:
                 current_salary *= r_post
             
             salaries[year] = current_salary

    return salaries

# UNIT TESTING: Test pre-retirement, retirement year (lump sum), post-retirement years, final year.
def linear_pension_draw_down_function(pot_value, current_year, retirement_year, final_year):
    """
    Calculates the amount to draw down from the pension pot based on a linear strategy.
    Note: This function now calculates 'Regular Income Drawdown' only. 
    Tax-free lump sum logic is handled externally in the simulation loop.

    Args:
        pot_value (float): The current value of the pension pot.
        current_year (int): The current year of the simulation.
        retirement_year (int): The year the individual retires.
        final_year (int): The final year of the simulation.

    Returns:
        float: The amount to withdraw from the pension pot.
    """
    # No drawdown before retirement
    if current_year < retirement_year:
        return 0

    # Linear drawdown after retirement
    else:
        # Calculate years left for drawdown (inclusive of current year)
        years_left = max(1, (final_year - current_year) + 1)
        return pot_value / years_left

# --- New Function for Desired Utility ---

# UNIT TESTING: Test with different years and rate combinations.
def calculate_desired_utility(year, start_year, baseline, linear_rate, exp_rate):
    """
    Calculates the desired utility spending for a given year based on parameters.

    Formula: (baseline + linear_rate * years_passed) * (1 + exp_rate) ** years_passed
    where years_passed is the number of years elapsed since the start_year.

    Args:
        year (int): The current simulation year.
        start_year (int): The first year of the simulation.
        baseline (float): The desired utility amount in the start_year.
        linear_rate (float): The absolute amount to add to the baseline each year.
        exp_rate (float): The exponential growth rate per year (e.g., 0.01 for 1%).

    Returns:
        float: The calculated desired utility for the given year.
    """
    years_passed = max(0, year - start_year)
    # Calculate the linearly adjusted baseline
    linear_adjusted_baseline = baseline + (linear_rate * years_passed)
    # Apply exponential growth to the linearly adjusted baseline
    desired_utility = linear_adjusted_baseline * ((1 + exp_rate) ** years_passed)
    return desired_utility


# UNIT TESTING: Test buy_utility (calculation, cash deduction), get_from_cash (overdraft penalty).
class Human:
    """Represents the individual being simulated."""
    def __init__(self, starting_cash, living_costs, pension_draw_down_function, non_linear_utility):
        """
        Initializes the Human object.

        Args:
            starting_cash (float): Initial cash amount.
            living_costs (dict): Dictionary of annual living costs {year: cost}.
            pension_draw_down_function (callable): Function to determine pension drawdown amount.
            non_linear_utility (float): Exponent for the utility function (diminishing returns).
        """
        self.cash = starting_cash
        self.living_costs = living_costs
        self.pension_draw_down_function = pension_draw_down_function
        self.non_linear_utility = non_linear_utility
        self.utility = [] # List to store annual utility values

    def buy_utility(self, amount):
        """Calculates utility from spending and deducts from cash."""
        if amount <= 0: # Cannot derive utility from zero or negative spending
             self.utility.append(0) # Append 0 utility
             return # Do not deduct cash

        # Utility function: amount ^ non_linear_utility (e.g., sqrt if 0.5)
        calculated_utility = amount**self.non_linear_utility
        self.utility.append(calculated_utility)
        self.cash -= amount

    def put_in_cash(self, amount_to_add):
        """Adds money to cash."""
        self.cash += amount_to_add

    def get_from_cash(self, amount_to_get):
        """
        Withdraws money from cash. Applies a penalty to utility if overdraft occurs.

        Args:
            amount_to_get (float): The amount requested.

        Returns:
            float: The amount actually withdrawn (can be less than requested if insufficient funds).
                   Returns the requested amount even if it causes overdraft.
        """
        if amount_to_get <= 0: return 0 # Cannot get zero or negative

        if amount_to_get > self.cash:
            logging.warning(msg=f"Not enough cash. Current: {self.cash:.2f}, Requested: {amount_to_get:.2f}. Overdraft occurred.")
            # Apply a quadratic penalty to the last recorded utility for going into overdraft
            overdraft_amount = amount_to_get - self.cash
            penalty = (overdraft_amount)**2
            if self.utility: # Check if utility list is not empty
                 self.utility[-1] -= penalty
                 print(f'Overdraft penalty {penalty:.2f} applied. Utility changed from {self.utility[-1] + penalty:.2f} to {self.utility[-1]:.2f}')
            else:
                 # Handle cases where utility list might be empty (e.g., first year issue)
                 self.utility.append(-penalty) # Start with penalty
                 print(f'Overdraft penalty applied as initial utility: {self.utility[-1]:.2f}')

            # Allow the withdrawal even if it results in negative cash
            self.cash -= amount_to_get
            return amount_to_get # Return the requested amount despite overdraft
        else:
            # Sufficient cash, proceed normally
            self.cash -= amount_to_get
            return amount_to_get


# UNIT TESTING: Test methods for calculating contributions and net salary.
class Employment:
    """Represents the employment status and income."""
    def __init__(self, gross_salary, employee_pension_contributions_pct=0.07, employer_pension_contributions_pct=0.07):
        """
        Initializes the Employment object.

        Args:
            gross_salary (dict): Dictionary of annual gross salaries {year: salary}.
            employee_pension_contributions_pct (float): Employee pension contribution rate.
            employer_pension_contributions_pct (float): Employer pension contribution rate.
        """
        self.gross_salary = gross_salary
        self.employee_pension_contributions_pct = employee_pension_contributions_pct
        self.employer_pension_contributions_pct = employer_pension_contributions_pct

    def get_salary_before_tax_after_pension_contributions(self, year):
        """Calculates salary subject to income tax (after employee pension contributions)."""
        gross = self.get_gross_salary(year)
        employee_contrib = gross * self.employee_pension_contributions_pct
        return gross - employee_contrib

    def get_gross_salary(self, year):
        """Retrieves the gross salary for a given year."""
        return self.gross_salary.get(year, 0) # Return 0 if year not in dict

    def get_employee_pension_contributions(self, year):
        """Calculates the employee's pension contribution amount for a given year."""
        return self.get_gross_salary(year) * self.employee_pension_contributions_pct

    def get_employer_pension_contributions(self, year):
        """Calculates the employer's pension contribution amount for a given year."""
        return self.get_gross_salary(year) * self.employer_pension_contributions_pct