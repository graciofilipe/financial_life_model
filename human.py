
class Human:
    def __init__(self, starting_cash, living_costs):
        self.cash = starting_cash
        self.living_costs = living_costs
    
    def put_in_cash(self, ammount_to_add):
        self.cash += ammount_to_add

    def get_from_cash(self, ammount_to_get):
        if ammount_to_get <= self.cash:
            self.cash -= ammount_to_get
            return ammount_to_get
        else:
            raise Exception("Insufficient funds")


class Employment:
    def __init__(self, gross_salary):
        self.gross_salary = gross_salary
        self.employee_pension_contributions_pct = 0.12
        self.employer_pension_contributions_pct = 0.07
    
    def get_salary(self, year):
        return self.gross_salary.get(year, 0) - self.gross_salary.get(year,0)*self.employee_pension_contributions_pct

    def get_gross_salary(self, year):
        return self.gross_salary.get(year, 0)

    def get_employee_pension_contributions(self, year):
        return self.gross_salary.get(year, 0) * self.employee_pension_contributions_pct
    
    def get_employer_pension_contributions(self, year):
        return self.gross_salary.get(year, 0) * self.employer_pension_contributions_pct


