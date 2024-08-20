from human import Human, Employment
from uk_gov import TaxMan
from investments_and_savings import PensionAccount, SotcksAndSharesISA, GeneralInvestmentAccount, FixedInterest





if __name__ == "__main__":

    ## set up my world ##

    my_employment = Employment(gross_salary=11000)
    my_fixed_interest = FixedInterest(initial_value=2000, interest_rate=0.02)
    my_NSI = FixedInterest(initial_value=5000, interest_rate=0.02)
    my_pension = PensionAccount(initial_value=10000, growth_rate=0.03)
    my_ISA = SotcksAndSharesISA(initial_value=10000, growth_rate=0.03)
    my_gia = GeneralInvestmentAccount(initial_value=10000)


    filipe = Human(yearly_living_costs=3000,
                   yearly_investment=0, 
                   yearly_saving=0,
                   cash=10000)

    hmrc = TaxMan()
    CGT_strategy = "harvest"

    for year in range(2024, 2034):
        print('for year ', year)
        
        
        ## get paid
        salary = my_employment.get_salary()
        
        # get UK gross interest
        gross_interest = my_fixed_interest.pay_interest() 
        nsi_interest = my_NSI.pay_interest()
        taxable_interest = hmrc.taxable_interest(taxable_income=salary, gross_interest=gross_interest)

        # get UK dividends # TODO: tax dividends
        dividends = 200

        # INVESTMENTS 
        my_ISA.grow_per_year()
        unrealised_capital_gains = my_gia.grow_per_year()
        
        if CGT_strategy == "harvest":
            capital_gains = unrealised_capital_gains
            capital_gains_tax = hmrc.capital_gains_tax_due(capital_gains)
        elif CGT_strategy == "let_grow":
            capital_gains_tax = 0

        money_for_ISA = filipe.get_from_cash(2000)
        my_ISA.put_money(money_for_ISA)
        money_for_gia = filipe.get_from_cash(2000)
        my_gia.put_money(money_for_gia)

        

        ## PENSIONS ##
        total_pension_contributions =  my_employment.get_employee_pension_contributions() + \
             my_employment.get_employer_pension_contributions()
                
        # allowance
        pension_allowance = hmrc.pension_allowance(taxable_income_post_pension=salary + taxable_interest,
                                                   individual_pension_contribution=my_employment.get_employee_pension_contributions(),
                                                   employer_contribution=my_employment.get_employer_pension_contributions())

        pension_pay_over_allowance = max(0, total_pension_contributions - pension_allowance)
        
        ## updates to pension pot
        my_pension.grow_per_year()
        my_pension.put_money(total_pension_contributions)
        

        ## PAY TAXES ##
        total_taxable_income = salary + taxable_interest + pension_pay_over_allowance
        print('total taxable income is ', total_taxable_income)

        tax_due = hmrc.calculate_uk_income_tax(total_taxable_income)
        ni_due = hmrc.calculate_uk_national_insurance(salary+ my_employment.get_employee_pension_contributions())
        all_tax = ni_due + tax_due + capital_gains_tax
        
        salary_after_tax = salary - all_tax

        ## PAY EXPENSES ##
        amount_needed_from_gia = max(filipe.yearly_living_costs - filipe.cash, 0)
        print('amount needed from gia is ', amount_needed_from_gia)
        extra_cash = my_gia.get_money(amount_needed_from_gia)
        filipe.put_in_cash(extra_cash)
        filipe.get_from_cash(filipe.yearly_living_costs)
        filipe.put_in_cash(salary_after_tax)



        print('your cash is: ', filipe.cash)
        print('your pension is: ', my_pension.asset_value)
        print('your ISA is: ', my_ISA.asset_value)
        print('your GIA is: ', my_gia.asset_value)

        print('\n')


