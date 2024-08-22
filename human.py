import logging


class Human:
    def __init__(self, starting_cash, living_costs, pension_draw_down_function):
        self.cash = starting_cash
        self.living_costs = living_costs
        self.pension_draw_down_function = pension_draw_down_function
        self.utility = []
    
    def buy_utility(self, ammount):
        self.utility.append(ammount)
        self.cash -= ammount



    def put_in_cash(self, ammount_to_add):
        self.cash += ammount_to_add

    def get_from_cash(self, ammount_to_get):
        self.cash -= ammount_to_get
        if self.cash < 0:
            logging.warning(msg=f"Cash is negative: {self.cash}")
        return ammount_to_get



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


