import logging


class Human:
    def __init__(self, starting_cash, living_costs, pension_draw_down_function, non_linear_utility):
        self.cash = starting_cash
        self.living_costs = living_costs
        self.pension_draw_down_function = pension_draw_down_function
        self.non_linear_utility = non_linear_utility
        self.utility = []
    
    def buy_utility(self, ammount):
        self.utility.append(ammount**self.non_linear_utility) ## some vaguely non linear diminishing returns to money
        self.cash -= ammount

    def put_in_cash(self, ammount_to_add):
        self.cash += ammount_to_add

    def get_from_cash(self, ammount_to_get):

        if ammount_to_get >= self.cash:
            logging.warning(msg=f"Not enough money in CASH: returned none")
            print('the amount I have is ', self.cash, ' but you asked me for ', ammount_to_get)
            print('the latest utility ', self.utility[-1])
            self.utility[-1] -= (self.cash - ammount_to_get)**2 # it hurts to go into overdraft
            print('now changed to ', self.utility[-1])
        self.cash -= ammount_to_get
        
        return ammount_to_get

class Employment:
    def __init__(self, gross_salary, employee_pension_contributions_pct=0.07, employer_pension_contributions_pct=0.07):
        self.gross_salary = gross_salary
        self.employee_pension_contributions_pct = employee_pension_contributions_pct
        self.employer_pension_contributions_pct = employer_pension_contributions_pct
    
    def get_salary_before_tax_after_pension_contributions(self, year):
        return self.gross_salary.get(year, 0) - self.gross_salary.get(year, 0)*self.employee_pension_contributions_pct

    def get_gross_salary(self, year):
        return self.gross_salary.get(year, 0)

    def get_employee_pension_contributions(self, year):
        return self.gross_salary.get(year, 0) * self.employee_pension_contributions_pct
    
    def get_employer_pension_contributions(self, year):
        return self.gross_salary.get(year, 0) * self.employer_pension_contributions_pct


