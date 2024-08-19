from human import Human, Employment
from uk_gov_classes import TaxMan




if __name__ == "__main__":

    my_employment = Employment(gross_salary=100000)

    filipe = Human(yearly_living_costs=50000, employment=my_employment, 
                yearly_investment=0, yearly_saving=0, cash=0)

    hmrc = TaxMan()

    for year in range(2024, 2054):
        
        salary = filipe.employment.get_gross_salary()
        
        tax_due = hmrc.calculate_uk_income_tax(salary)
        
        salary_after_tax = salary - tax_due
        
        filipe.put_in_cash(salary_after_tax)
        
        filipe.get_from_cash(filipe.yearly_living_costs)

    print(filipe.cash)

