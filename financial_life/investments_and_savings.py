import logging
import math # Import math for isnan check

class DisposableCash:
    """Represents readily available cash, not subject to investment growth or interest."""
    def __init__(self, initial_value=0):
        self.asset_value = initial_value

    def put_money(self, amount):
        """Adds money."""
        self.asset_value += amount

    def get_money(self, amount):
        """Withdraws money if sufficient funds exist."""
        if amount <= self.asset_value:
            self.asset_value -= amount
            return amount
        else:
            logging.warning(msg=f"Insufficient disposable cash. Requested: {amount}, Available: {self.asset_value}")
            # Return the amount available instead of raising error or returning string
            available_amount = self.asset_value
            self.asset_value = 0
            return available_amount


class StocksAndSharesISA:
    """Represents a Stocks and Shares ISA account (tax-free growth)."""
    def __init__(self, initial_value=0, growth_rate=0.03):
        """
        Initializes the ISA.

        Args:
            initial_value (float): Starting value of the ISA.
            growth_rate (float): Assumed annual growth rate (e.g., 0.03 for 3%).
        """
        self.asset_value = initial_value
        self.growth_rate = growth_rate

    def put_money(self, amount):
        """Adds money to the ISA."""
        if amount > 0:
            self.asset_value += amount

    def get_money(self, amount):
        """Withdraws money from the ISA if sufficient funds exist."""
        if amount <= self.asset_value:
            self.asset_value -= amount
            return amount
        else:
            logging.warning(msg=f"Insufficient funds in ISA. Requested: {amount}, Available: {self.asset_value}. Returning 0.")
            return 0 # Return 0 to indicate failure clearly

    def grow_per_year(self):
        """Applies the annual growth rate to the asset value."""
        self.asset_value *= (1 + self.growth_rate)


class PensionAccount:
    """Represents a Pension account (tax relief on contribution, growth is tax-deferred)."""
    def __init__(self, initial_value=0, growth_rate=0.03):
        """
        Initializes the Pension account.

        Args:
            initial_value (float): Starting value of the pension pot.
            growth_rate (float): Assumed annual growth rate.
        """
        self.asset_value = initial_value
        self.growth_rate = growth_rate

    def put_money(self, amount):
        """Adds money to the pension pot."""
        if amount > 0:
            self.asset_value += amount

    def get_money(self, amount):
        """Withdraws money from the pension pot if sufficient funds exist."""
        # Note: Tax implications of withdrawal are handled outside this class (in simulation logic).
        if amount <= self.asset_value:
            self.asset_value -= amount
            return amount
        else:
            logging.warning(msg=f"Insufficient funds in Pension. Requested: {amount}, Available: {self.asset_value}. Returning 0.")
            return 0 # Return 0 clearly

    def grow_per_year(self):
        """Applies the annual growth rate to the asset value."""
        self.asset_value *= (1 + self.growth_rate)


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

        # Handle potential division by zero or invalid inputs for initial prices
        if self.units > 0 and self.asset_value >= 0:
            # If average buy price is provided and valid, use it.
            if initial_average_buy_price > 0:
                 self.average_unit_buy_price = float(initial_average_buy_price)
                 # Set current price based on initial value and units, could differ from avg buy price
                 self.current_unit_price = self.asset_value / self.units
            else:
                 # If no valid buy price provided, calculate from value and units
                 self.average_unit_buy_price = self.asset_value / self.units
                 self.current_unit_price = self.average_unit_buy_price # Assume current price = avg buy price initially
        elif self.units == 0 and self.asset_value == 0:
             # Empty account initialization
             self.average_unit_buy_price = 0.0
             self.current_unit_price = 1.0 # Assign a nominal starting price (e.g., 1) for future buys
        else:
             # Inconsistent state (e.g., value without units or vice-versa) - log warning
             logging.warning(f"Inconsistent GIA initial state: Value={self.asset_value}, Units={self.units}. Resetting prices.")
             # Reset to a safe state or raise an error? Resetting for now.
             self.average_unit_buy_price = 0.0
             self.current_unit_price = 1.0 # Nominal price

        # Ensure prices are not NaN if calculations resulted in it
        if math.isnan(self.average_unit_buy_price): self.average_unit_buy_price = 0.0
        if math.isnan(self.current_unit_price): self.current_unit_price = 1.0


    def put_money(self, amount):
        """Adds money to the GIA, buying units at the current price."""
        if amount <= 0 or self.current_unit_price <= 0:
            # Cannot invest zero/negative amount or if price is non-positive
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
        if self.units < 1e-9:
            self.units = 0
            self.asset_value = 0
            self.average_unit_buy_price = 0 # Reset average price if empty
        elif self.units > 0 and self.asset_value < 1e-9:
             # If units exist but value is near zero, recalculate value
             self.asset_value = self.units * self.current_unit_price


        return actual_amount_removed, max(0, capital_gains) # Ensure gains aren't negative

    def grow_per_year(self):
        """Applies annual growth to the unit price and updates asset value."""
        # Only grow if there are units
        if self.units > 0:
            self.current_unit_price *= (1 + self.growth_rate)
            self.asset_value = self.units * self.current_unit_price
        else:
            # If no units, value should be zero
            self.asset_value = 0


class FixedInterest:
    """Represents a simple fixed interest savings account (interest is taxable)."""
    def __init__(self, initial_value=0, interest_rate=0.02):
        """
        Initializes the Fixed Interest account.

        Args:
            initial_value (float): Starting balance.
            interest_rate (float): Annual interest rate (e.g., 0.02 for 2%).
        """
        self.asset_value = initial_value
        self.interest_rate = interest_rate

    def put_money(self, amount):
        """Adds money."""
        if amount > 0:
            self.asset_value += amount

    def get_money(self, amount):
        """Withdraws money if sufficient funds exist."""
        if amount <= self.asset_value:
            self.asset_value -= amount
            return amount
        else:
            logging.warning(msg=f"Insufficient funds in Fixed Interest. Requested: {amount}, Available: {self.asset_value}. Returning available.")
            available_amount = self.asset_value
            self.asset_value = 0
            return available_amount # Return what's available

    def pay_interest(self):
        """Calculates the gross interest earned for the year."""
        # Note: Does not add to asset_value here; simulation logic handles adding to cash.
        # Tax is handled outside this class.
        return self.asset_value * self.interest_rate
