import logging
import math # Import math for isnan check

# --- Functions moved from setup_world.py ---

def generate_living_costs():
    """Generates a dictionary of projected annual living costs."""
    r1 = 1.02 # rate of increase until retirement
    r2 = 1.04 # rate of increase after retirement
    retirement_year = 2055 # Assuming retirement year for cost split - consider making this dynamic?
    final_sim_year = 2074 # Assuming final year - consider making this dynamic?

    # Costs increase at rate r1 until retirement year
    d1 = {year: 20000 * (r1)**idx for idx, year in enumerate(range(2025, retirement_year + 1))}
    # Costs increase at rate r2 from the year after retirement
    # Base cost for post-retirement is the cost in the retirement year
    base_post_retirement_cost = d1[retirement_year]
    d2 = {year: base_post_retirement_cost * (r2)**idx for idx, year in enumerate(range(retirement_year + 1, final_sim_year + 1), start=1)}
    # Combine the two dictionaries
    return {**d1, **d2}

def generate_salary():
    """Generates a dictionary of projected annual gross salaries."""
    r = 1.01 # salary growth rate
    retirement_year = 2054 # Assuming last year of work is 2054
    # Salary increases at rate r from 2024 up to and including retirement_year
    return {year: 100000 * (r)**idx for idx, year in enumerate(range(2024, retirement_year + 1))}

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


# --- Original Classes ---

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
