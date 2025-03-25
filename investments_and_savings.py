import logging


class DisposableCash:
    def __init__(self, initial_value=0):
        self.asset_value = initial_value

    def put_money(self, amount):
        self.asset_value += amount

    def get_money(self, amount):
        if amount <= self.asset_value:
            self.asset_value -= amount
            return amount
        else:
            return "Insufficient funds"



class SotcksAndSharesISA:
    def __init__(self, initial_value=0, growth_rate=0.03):
        self.asset_value = initial_value
        self.growth_rate = growth_rate

    def put_money(self, amount):
        self.asset_value += amount

    def get_money(self, amount):
        if amount <= self.asset_value:
            self.asset_value -= amount
            return amount
        else:
            logging.warning(msg=f"Not enough money in ISA: none taken")
            return 0

    def grow_per_year(self):
        self.asset_value *= (1+self.growth_rate)



class PensionAccount:
    def __init__(self, initial_value=0, growth_rate=0.03):
        self.asset_value = initial_value
        self.growth_rate = growth_rate


    def put_money(self, amount):
        self.asset_value += amount

    def get_money(self, amount):
        if amount <= self.asset_value:
            self.asset_value -= amount
            return amount
        else:
            logging.warning(msg=f"Not enough money in Pension: none taken")
            return 0

    def grow_per_year(self):
        self.asset_value *= (1+self.growth_rate)


class GeneralInvestmentAccount:
    def __init__(self, initial_value=0, initial_units=100.0, growth_rate=0.03):
        self.asset_value = initial_value
        self.growth_rate = growth_rate
        self.units=initial_units
        self.average_unit_buy_price = self.asset_value/initial_units
        self.current_unit_price = self.average_unit_buy_price

    def put_money(self, amount):
        if amount == 0:
            pass
        else:
            units_to_add = amount/self.current_unit_price
            self.average_unit_buy_price = (self.units*self.average_unit_buy_price + units_to_add*self.current_unit_price) / (self.units + units_to_add)
            self.asset_value += amount
            self.units += units_to_add

    def get_money(self, amount):
        if amount <= self.asset_value:
            units_to_remove = amount/self.current_unit_price
            self.asset_value -= amount
            self.units -= units_to_remove
            capital_gains = (units_to_remove * self.current_unit_price) - (units_to_remove * self.average_unit_buy_price)
            return amount, capital_gains
        else:
            logging.warning(msg=f"Not enough money in ISA: none taken")
            return 0

    def grow_per_year(self):
        self.units = max(0, self.units)
        self.current_unit_price = self.current_unit_price * (1+self.growth_rate)
        self.asset_value = self.units * self.current_unit_price
        
    


class FixedInterest:
    def __init__(self, initial_value=0, interest_rate=0.02):
        self.asset_value = initial_value
        self.interest_rate = interest_rate

    def put_money(self, amount):
        self.asset_value += amount

    def get_money(self, amount):
        if amount <= self.asset_value:
            self.asset_value -= amount
            return amount
        else:
            return "Insufficient funds"

    def pay_interest(self):
        return self.asset_value * self.interest_rate