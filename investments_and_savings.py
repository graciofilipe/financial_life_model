

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
            return "Insufficient funds"

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
            return "Insufficient funds"

    def grow_per_year(self):
        self.asset_value *= (1+self.growth_rate)



class GeneralInvestmentAccount:
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
            return "Insufficient funds"

    def grow_per_year(self):
        growth = self.asset_value * self.growth_rate
        self.asset_value += growth
        return growth
        
    





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