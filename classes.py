




class GeneralInvestmentAccount:
    def __init__(self, initial_value=0, starting_year=2024):
        self.asset_value = initial_value
        self.starting_year = start_year

    def put_money(self, amount):
        self.asset_value += amount

    def get_money(self, amount):
        if amount <= self.asset_value:
            self.asset_value -= amount
            return amount
        else:
            return "Insufficient funds"

    def grow_per_year(self, r):
        self.asset_value *= (1 + r)



class NSandI:
    def __init__(self, initial_value=0, interest_rate=0.02, starting_year=2024):
        self.asset_value = initial_value
        self.interest_rate = interest_rate
        self.starting_year = start_year

    def put_money(self, amount):
        self.asset_value += amount

    def get_money(self, amount):
        if amount <= self.asset_value:
            self.asset_value -= amount
            return amount
        else:
            return "Insufficient funds"

    def grow_per_year(self):
        self.asset_value *= (1 + self.interest_rate)


