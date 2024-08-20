
class Human:
    def __init__(self,yearly_living_costs,
                 yearly_investment, yearly_saving, cash):
        
        self.yearly_living_costs = yearly_living_costs
        self.yearly_investment = yearly_investment
        self.yearly_saving = yearly_saving
        self.cash = cash

    def put_in_cash(self, ammount_to_add):
        self.cash += ammount_to_add

    def get_from_cash(self, ammount_to_get):
        if ammount_to_get <= self.cash:
            self.cash -= ammount_to_get
            return ammount_to_get
        else:
            raise Exception("Insufficient funds")


    def put_in_GIA(self, ammount_to_invest, GIA_object):
        GIA_object.put_money(ammount_to_invest)

    def get_from_GIA(self, ammount_to_get, GIA_object):
        GIA_object.get_money(ammount_to_get)




class Employment:
    def __init__(self, gross_salary):
        self.gross_salary = gross_salary
        self.employee_pension_contributions = 0.12
        self.employer_pension_contributions = 0.07
    
    def get_salary(self):
        return self.gross_salary - self.gross_salary*self.employee_pension_contributions

    def get_gross_salary(self):
        return self.gross_salary

    def get_employee_pension_contributions(self):
        return self.employee_pension_contributions
    
    def get_employer_pension_contributions(self):
        return self.employer_pension_contributions


