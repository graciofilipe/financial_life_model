from human import Human, Employment
from uk_gov import TaxMan
from investments_and_savings import PensionAccount, SotcksAndSharesISA, GeneralInvestmentAccount, FixedInterest
from setup_world import generate_living_costs, generate_salary





if __name__ == "__main__":

    ## set up my world ##

    my_employment = Employment(gross_salary=generate_salary())
    my_fixed_interest = FixedInterest(initial_value=20000, interest_rate=0.02)
    my_NSI = FixedInterest(initial_value=50000, interest_rate=0.02)
    my_pension = PensionAccount(initial_value=100000, growth_rate=0.03, pension_draw_down)
    my_ISA = SotcksAndSharesISA(initial_value=100000, growth_rate=0.03)
    my_gia = GeneralInvestmentAccount(initial_value=100000, growth_rate=0.03)


    filipe = Human(starting_cash=10000, living_costs=generate_living_costs())

    hmrc = TaxMan()
    CGT_strategy = "harvest"

    for year in range(2024, 2074):
        print('for year ', year)
                
        ## get paid
        taxable_salary = my_employment.get_salary(year)
        print('taxable salary is ', taxable_salary)
        
        # get UK gross interest
        gross_interest = my_fixed_interest.pay_interest() 
        print('gross interest is ', gross_interest)
        nsi_interest = my_NSI.pay_interest()
        taxable_interest = hmrc.taxable_interest(taxable_income=taxable_salary, gross_interest=gross_interest)
        print('taxable interest is ', taxable_interest)
        
        # get UK dividends # TODO: tax dividends
        dividends = 200

        # INVESTMENTS 
        my_ISA.grow_per_year()
        unrealised_capital_gains = my_gia.grow_per_year()
        if CGT_strategy == "harvest":
            capital_gains = unrealised_capital_gains
            capital_gains_tax = hmrc.capital_gains_tax_due(capital_gains)
            print('capital gains tax is ', capital_gains_tax)
        elif CGT_strategy == "let_grow":
            capital_gains_tax = 0

        money_for_ISA = filipe.get_from_cash(2000)
        my_ISA.put_money(money_for_ISA)
        money_for_gia = filipe.get_from_cash(2000)
        my_gia.put_money(money_for_gia)

        

        ## PENSIONS ##
        total_pension_contributions =  my_employment.get_employee_pension_contributions(year) + \
             my_employment.get_employer_pension_contributions(year)
        print('total pension contributions is ', total_pension_contributions)
                
        # allowance
        pension_allowance = hmrc.pension_allowance(taxable_income_post_pension=salary + taxable_interest,
                                                   individual_pension_contribution=my_employment.get_employee_pension_contributions(year),
                                                   employer_contribution=my_employment.get_employer_pension_contributions(year))

        print('pension allowance is ', pension_allowance)

        pension_pay_over_allowance = max(0, total_pension_contributions - pension_allowance)
        print('pension_pay_over_allowance allowance is ', pension_pay_over_allowance)

        
        ## updates to pension pot
        my_pension.grow_per_year()
        my_pension.put_money(total_pension_contributions)
        

        ## PAY TAXES ##
        total_taxable_income = taxable_salary + taxable_interest + pension_pay_over_allowance
        print('total taxable income is ', total_taxable_income)

        tax_due = hmrc.calculate_uk_income_tax(total_taxable_income)
        print('tax due is ', tax_due)


        ni_due = hmrc.calculate_uk_national_insurance(taxable_salary+ my_employment.get_employee_pension_contributions(year))
        print(f'NI due is {ni_due}')

        all_tax = ni_due + tax_due + capital_gains_tax
        print('all tax is ', all_tax)
        
        salary_after_tax = salary - all_tax
        print('salary after tax is ', salary_after_tax)


        ## PAY EXPENSES ##
        amount_needed_from_gia = max(filipe.living_costs[year]*1.5 - filipe.cash, 0)
        print('amount needed from gia is ', amount_needed_from_gia)
        extra_cash = my_gia.get_money(amount_needed_from_gia)
        filipe.put_in_cash(extra_cash)
        filipe.get_from_cash(filipe.living_costs[year])
        filipe.put_in_cash(salary_after_tax)



        print('your cash is: ', round(filipe.cash))
        print('your pension is: ', round(my_pension.asset_value))
        print('your ISA is: ', round(my_ISA.asset_value))
        print('your GIA is: ', round(my_gia.asset_value))

        print('\n')


