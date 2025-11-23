import logging
import math # Import math for isnan check

# UNIT TESTING: Test grow_per_year, basic put_money/get_money (especially edge cases like zero/negative amounts, insufficient funds).
class InvestmentAccountBase:
    """Base class for investment accounts."""
    def __init__(self, initial_value=0.0, growth_rate=0.0):
        self.asset_value = float(initial_value)
        self.growth_rate = float(growth_rate)

    def grow_per_year(self):
        """
        Applies the annual growth rate to the asset value.
        """
        self.asset_value *= (1 + self.growth_rate)

    def put_money(self, amount):
        """
        Adds money to the account.
        
        Args:
            amount (float): The amount to add.
        """
        if amount > 0:
            self.asset_value += amount
        else:
            logging.warning(f"Cannot put non-positive amount: {amount} into {self.__class__.__name__}")

    def get_money(self, amount):
        """
        Withdraws money from the account.
        
        Args:
            amount (float): The amount to withdraw.

        Returns:
            float: The amount withdrawn.
        """
        if amount <= 0:
            logging.warning(f"Cannot get non-positive amount: {amount} from {self.__class__.__name__}")
            return 0
        if amount <= self.asset_value:
            self.asset_value -= amount
            return amount
        else:
            # Default behavior for insufficient funds, can be overridden
            logging.warning(f"Insufficient funds in {self.__class__.__name__}. Requested: {amount}, Available: {self.asset_value}. Returning 0.")
            return 0

# UNIT TESTING: Test __init__, overridden get_money.
class DisposableCash(InvestmentAccountBase):
    """Represents readily available cash, not subject to investment growth or interest."""
    def __init__(self, initial_value=0):
        super().__init__(initial_value=initial_value, growth_rate=0)

    def get_money(self, amount):
        """
        Withdraws money if sufficient funds exist.
        
        Args:
            amount (float): The amount to withdraw.

        Returns:
            float: The amount withdrawn. Returns the total available if requested amount exceeds balance.
        """
        if amount <= 0: # Keep this check or rely on base
            logging.warning(f"Cannot get non-positive amount: {amount} from {self.__class__.__name__}")
            return 0
        if amount <= self.asset_value:
            self.asset_value -= amount
            return amount
        else:
            logging.warning(msg=f"Insufficient funds in {self.__class__.__name__}. Requested: {amount}, Available: {self.asset_value}. Returning available.")
            available_amount = self.asset_value
            self.asset_value = 0
            return available_amount


class StocksAndSharesISA(InvestmentAccountBase):
    """Represents a Stocks and Shares ISA account (tax-free growth)."""
    def __init__(self, initial_value=0, growth_rate=0.03):
        """
        Initializes the ISA.

        Args:
            initial_value (float): Starting value of the ISA.
            growth_rate (float): Assumed annual growth rate (e.g., 0.03 for 3%).
        """
        super().__init__(initial_value, growth_rate)
        # put_money and get_money can be inherited from InvestmentAccountBase


class PensionAccount(InvestmentAccountBase):
    """Represents a Pension account (tax relief on contribution, growth is tax-deferred)."""
    def __init__(self, initial_value=0, growth_rate=0.03):
        """
        Initializes the Pension account.

        Args:
            initial_value (float): Starting value of the pension pot.
            growth_rate (float): Assumed annual growth rate.
        """
        super().__init__(initial_value, growth_rate)
        # put_money and get_money can be inherited from InvestmentAccountBase
        # grow_per_year is inherited from InvestmentAccountBase


# UNIT TESTING: Thoroughly test __init__ (various initial states), put_money (updates to units, avg_price, value), 
# get_money (units sold, capital gains, state updates), grow_per_year. Cover edge cases like selling all units, zero balances.
class GeneralInvestmentAccount:
    """Represents a General Investment Account (subject to Capital Gains Tax)."""
    def __init__(self, initial_value=0, initial_units=0, initial_average_buy_price=1, growth_rate=0.03):
        """
        Initializes the GIA.

        Args:
            initial_value (float): Starting total value of the GIA.
            initial_units (float): Starting number of units held.
            initial_average_buy_price (float): The average price at which the initial units were acquired.
            growth_rate (float): Assumed annual growth rate of the underlying assets.
        """
        self.asset_value = float(initial_value)
        self.units = float(initial_units)
        self.growth_rate = float(growth_rate)

        # Determine initial prices
        if self.units > 0:
            # If initial_average_buy_price is provided and valid, prioritize it
            if initial_average_buy_price is not None and initial_average_buy_price > 0:
                self.average_unit_buy_price = float(initial_average_buy_price)
                # Current unit price is based on the total asset value and units
                self.current_unit_price = self.asset_value / self.units
            # Else, derive average_unit_buy_price from initial_value and initial_units
            elif self.asset_value >= 0 : # self.units > 0 is already true here
                self.average_unit_buy_price = self.asset_value / self.units
                self.current_unit_price = self.average_unit_buy_price
            else: # Fallback for inconsistent data (e.g. negative asset_value with positive units)
                logging.warning(f"Inconsistent GIA initial state: Value={self.asset_value}, Units={self.units}. Setting prices to 0.")
                self.average_unit_buy_price = 0.0
                self.current_unit_price = 0.0
        elif self.units == 0: # No units
            self.average_unit_buy_price = 0.0
            if self.asset_value == 0: # No units and no value - standard empty account
                self.current_unit_price = 1.0 # Default for future buys
            else: # No units but has value - inconsistent state
                logging.warning(f"Inconsistent GIA initial state: Value={self.asset_value}, Units={self.units}. Current price set to 0.")
                self.current_unit_price = 0.0 # Or handle as an error
        else: # Negative units - invalid state
            logging.error(f"Invalid GIA initial state: Units={self.units}. Resetting prices to 0.")
            self.average_unit_buy_price = 0.0
            self.current_unit_price = 0.0
            self.asset_value = 0.0 # Also reset asset value if units are negative
            self.units = 0.0


    def put_money(self, amount):
        """
        Adds money to the GIA, buying units at the current price.

        Args:
            amount (float): The amount to invest.
        """
        if amount <= 0 or self.current_unit_price <= 0:
            # Cannot invest zero/negative amount or if price is non-positive
            logging.warning(f"Cannot put non-positive amount or use non-positive price for GIA. Amount: {amount}, Price: {self.current_unit_price}")
            return

        units_to_add = amount / self.current_unit_price
        # Update average buy price: (Total old cost + New cost) / Total new units
        new_total_units = self.units + units_to_add
        if new_total_units > 0: # Avoid division by zero
            self.average_unit_buy_price = ((self.units * self.average_unit_buy_price) + (units_to_add * self.current_unit_price)) / new_total_units
        else:
             # Should not happen if units_to_add > 0, but as safety
             self.average_unit_buy_price = self.current_unit_price

        self.asset_value += amount
        self.units += units_to_add

    def get_money(self, amount):
        """
        Withdraws money by selling units, calculating capital gains.

        Args:
            amount (float): The amount of money to withdraw.

        Returns:
            tuple: (amount_received, capital_gains) if successful.
            float: 0 if insufficient funds or invalid request.
        """
        if amount <= 0:
            logging.warning(f"Cannot get non-positive amount: {amount} from GIA")
            return 0 # Cannot withdraw zero/negative

        if amount > self.asset_value or self.current_unit_price <= 0 or self.units <= 0:
            logging.warning(f"Insufficient funds or invalid state in GIA. Requested: {amount}, Available: {self.asset_value}. Units: {self.units}. Price: {self.current_unit_price}. Returning 0.")
            return 0 # Insufficient funds or cannot sell

        units_to_remove = amount / self.current_unit_price

        # Ensure we don't sell more units than we have due to floating point issues
        units_to_remove = min(units_to_remove, self.units)
        actual_amount_removed = units_to_remove * self.current_unit_price

        # Calculate capital gains on the units sold
        cost_of_units_sold = units_to_remove * self.average_unit_buy_price
        capital_gains = actual_amount_removed - cost_of_units_sold

        # Update account state
        self.asset_value -= actual_amount_removed
        self.units -= units_to_remove

        # Handle potential floating point inaccuracies leading to tiny negative values
        if self.units < 1e-9: # Consider a small epsilon for float comparison
            self.units = 0.0
            self.asset_value = 0.0
            self.average_unit_buy_price = 0.0 # Reset average price if empty
        elif self.units > 0 and self.asset_value < 1e-9: # Similar check for asset_value
             self.asset_value = 0.0 # Or recalculate: self.units * self.current_unit_price


        return actual_amount_removed, max(0.0, capital_gains) # Ensure gains aren't negative

    def grow_per_year(self):
        """
        Applies annual growth to the unit price and updates asset value.
        """
        # Only grow if there are units
        if self.units > 0:
            self.current_unit_price *= (1 + self.growth_rate)
            self.asset_value = self.units * self.current_unit_price
        else:
            # If no units, value should be zero, current_unit_price can still grow
            self.current_unit_price *= (1 + self.growth_rate) # Price can grow even with no units
            self.asset_value = 0.0


# UNIT TESTING: Test __init__, overridden get_money, pay_interest().
class FixedInterest(InvestmentAccountBase):
    """Represents a simple fixed interest savings account (interest is taxable)."""
    def __init__(self, initial_value=0, interest_rate=0.02):
        """
        Initializes the Fixed Interest account.

        Args:
            initial_value (float): Starting balance.
            interest_rate (float): Annual interest rate (e.g., 0.02 for 2%).
        """
        super().__init__(initial_value=initial_value, growth_rate=0) # Fixed interest doesn't grow via growth_rate
        self.interest_rate = interest_rate

    def get_money(self, amount):
        """
        Withdraws money if sufficient funds exist.
        
        Args:
            amount (float): The amount to withdraw.

        Returns:
            float: The amount withdrawn. Returns the total available if requested amount exceeds balance.
        """
        if amount <= 0: # Keep this check or rely on base
            logging.warning(f"Cannot get non-positive amount: {amount} from {self.__class__.__name__}")
            return 0
        if amount <= self.asset_value:
            self.asset_value -= amount
            return amount
        else:
            logging.warning(msg=f"Insufficient funds in {self.__class__.__name__}. Requested: {amount}, Available: {self.asset_value}. Returning available.")
            available_amount = self.asset_value
            self.asset_value = 0
            return available_amount # Return what's available

    def pay_interest(self):
        """
        Calculates the gross interest earned for the year based on the current balance.

        Returns:
            float: The gross interest amount.
        """
        # Note: Does not add to asset_value here; simulation logic handles adding to cash.
        # Tax is handled outside this class.
        return self.asset_value * self.interest_rate