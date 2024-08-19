from human import Human, Employment
from uk_gov import TaxMan
from investments_and_savings import PensionAccount, SotcksAndSharesISA






if __name__ == "__main__":

    ## set up my world ##

    my_employment = Employment(gross_salary=100000)
    my_pension = PensionAccount(initial_value=100000, growth_rate=1.03)
    my_ISA = SotcksAndSharesISA(initial_value=100000, growth_rate=1.03)


    filipe = Human(yearly_living_costs=50000,
                   yearly_investment=0, 
                   yearly_saving=0,
                   cash=100000)

    hmrc = TaxMan()

    for year in range(2024, 2054):
        
        ## get paid
        gross_salary = my_employment.get_gross_salary()
        
         
        ## updates to pension
        pension_deduction = 20000
        my_pension.grow_per_year()
        my_pension.put_money(pension_deduction)
        taxable_income = gross_salary - pension_deduction
                
        tax_due = hmrc.calculate_uk_income_tax(taxable_income)
        ni_due = hmrc.calculate_uk_national_insurance(taxable_income)
        all_tax = ni_due + tax_due
        
        salary_after_tax = taxable_income - all_tax

        ## PAY EXPENSES ##
        filipe.get_from_cash(filipe.yearly_living_costs)


        # INVESTMENTS #
        money_for_ISA = filipe.get_from_cash(20000)
        my_ISA.grow_per_year()
        my_ISA.put_money(money_for_ISA)



        filipe.put_in_cash(salary_after_tax)


    print('your cash is: ', filipe.cash)
    print('your pension is: ', my_pension.asset_value)
    print('your ISA is: ', my_ISA.asset_value)

