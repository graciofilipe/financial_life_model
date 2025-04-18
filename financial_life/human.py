import logging
import math # Import math for isnan check


def generate_living_costs(base_cost, base_year, rate_pre_retirement, rate_post_retirement, retirement_year, final_year):
    """
    Generates a dictionary of projected annual living costs based on provided rates and years.

    Args:
        base_cost (float): The living cost in the base_year.
        base_year (int): The year corresponding to the base_cost.
        rate_pre_retirement (float): Annual rate of living cost increase before retirement (e.g., 0.02 for 2%).
        rate_post_retirement (float): Annual rate of living cost increase after retirement (e.g., 0.04 for 4%).
        retirement_year (int): The year retirement occurs. Costs increase at the pre-retirement rate up to and including this year.
        final_year (int): The final year of the simulation for which costs are calculated.

    Returns:
        dict: A dictionary where keys are years (int) and values are projected living costs (float).
    """
    r1 = 1 + rate_pre_retirement # Convert rate to multiplier
    r2 = 1 + rate_post_retirement # Convert rate to multiplier

    # Costs increase at rate r1 until retirement year (inclusive)
    # Uses the provided base_cost and base_year
    start_year = base_year # Use the provided base_year
    # The base_cost argument is used directly in the calculation below

    # Calculate costs from base_year up to retirement_year
    d1 = {year: base_cost * (r1)**(year - start_year) for year in range(start_year, retirement_year + 1)}

    # Costs increase at rate r2 from the year after retirement
    if retirement_year in d1: # Check if retirement happened within the calculated range
        base_post_retirement_cost = d1[retirement_year]
        d2 = {year: base_post_retirement_cost * (r2)**(year - retirement_year) for year in range(retirement_year + 1, final_year + 1)}
    else: # Handle cases where retirement year might be before the start year (edge case)
         # If retirement is before the cost calculation starts, apply post-retirement rate from the start
          # This assumes costs still start being tracked from base_year
         # A more robust approach might need a different base cost calculation
          base_post_retirement_cost = base_cost * (r1)**(retirement_year - base_year) # Hypothetical cost at retirement
          d2 = {year: base_post_retirement_cost * (r2)**(year - retirement_year) for year in range(base_year, final_year + 1)}
         d1 = {} # No pre-retirement costs in this scenario within the tracked range

    # Combine the two dictionaries
    return {**d1, **d2}

def generate_salary(base_salary, base_year, growth_rate, last_work_year):
    """
    Generates a dictionary of projected annual gross salaries based on a growth rate and final work year.

    Args:
        base_salary (float): The gross salary in the base_year.
        base_year (int): The year corresponding to the base_salary.
        growth_rate (float): Annual salary growth rate (e.g., 0.01 for 1%).
        last_work_year (int): The final year the salary is earned.

    Returns:
        dict: A dictionary where keys are years (int) and values are projected gross salaries (float).
    """
    r = 1 + growth_rate # Convert rate to multiplier
    # Uses the provided base_salary and base_year
    start_year = base_year # Use the provided base_year
    # The base_salary argument is used directly in the calculation below
    # Salary increases at rate r from start_year up to and including last_work_year
    return {year: base_salary * (r)**(year - start_year) for year in range(start_year, last_work_year + 1)}

def linear_pension_draw_down_function(pot_value, current_year, retirement_year, final_year):
    """
    Calculates the amount to draw down from the pension pot based on a linear strategy.
    Takes a 25% tax-free lump sum at retirement, then draws down linearly.
    """
    # Take tax-free lump sum at retirement (up to 25% or LTA cap, simplified here)
    if current_year == retirement_year:
        # Simplified max lump sum - LTA rules are complex and changing
        lump_sum_allowance = 268275 # Approx 25% of previous £1,073,100 LTA (use current rules if needed)
        return min(0.25 * pot_value, lump_sum_allowance)

    # No drawdown before retirement
    elif current_year < retirement_year:
        return 0

    # Linear drawdown after retirement (excluding the retirement year itself)
    else:
        # Calculate remaining pot after potential lump sum taken in retirement year
        # This requires knowing the pot value *at the start* of the retirement year
        # The current function design doesn't easily allow this lookback.
        # Simplification: Assume the pot_value passed already excludes the lump sum if current_year > retirement_year.
        # This might lead to inaccurate drawdown if called mid-year after growth.
        # A better design might pass the simulation state or specific pot values.

        # Calculate years left for drawdown (inclusive of current year, exclusive of final year?)
        # If final_year is 2074, and current is 2074, years_left should be 1.
        years_left = max(1, (final_year - current_year) + 1)
        return pot_value / years_left

# --- New Function for Desired Utility ---

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
