from human import Employment, Human
from uk_gov import TaxMan
from investments_and_savings import PensionAccount, SotcksAndSharesISA, GeneralInvestmentAccount, FixedInterest
from setup_world import generate_living_costs, generate_salary, linear_pension_draw_down_function
import logging
import pandas as pd
import argparse
import os
from datetime import datetime
from aux_funs import get_last_element_or_zero
import plotly.express as px
from google.cloud import storage


def simulate_a_life(args):

    taxable_salary_list = []
    gross_interest_list = []
    taxable_interest_list = []
    capital_gains_list = []
    capital_gains_tax_list = []
    pension_allowance_list = []
    pension_pay_over_allowance_list = []
    taken_from_pension_list = []
    total_taxable_income_list = []
    income_tax_due_list = []
    national_insurance_due_list = []
    all_tax_list = []
    income_after_tax_list = []
    cash_list = []
    pension_allowance_list
    pension_list = []
    ISA_list = []
    GIA_list = [] 
    living_costs_list = []
    ammount_needed_from_gia_list = []
    TOTAL_ASSETS_list = []
    money_invested_in_ISA = []
    money_invested_in_GIA = []

    #bucket_name = args.bucket_name

    ## set up my world ##
    my_employment = Employment(gross_salary=generate_salary())
    my_fixed_interest = FixedInterest(initial_value=args.fixed_interest_capital, interest_rate=args.fixed_interest_rate)
    my_NSI = FixedInterest(initial_value=args.NSI_capital, interest_rate=args.NSI_interest_rate)
    my_pension = PensionAccount(initial_value=args.pension_capital, growth_rate=args.pension_growth_rate)
    my_ISA = SotcksAndSharesISA(initial_value=args.ISA_capital, growth_rate=args.ISA_growth_rate)
    my_gia = GeneralInvestmentAccount(initial_value=args.GIA_capital, growth_rate=args.GIA_growth_rate)


    filipe = Human(starting_cash=args.starting_cash,
                   living_costs=generate_living_costs(), 
                   pension_draw_down_function=linear_pension_draw_down_function)

    hmrc = TaxMan()
    
    for year in range(args.start_year, args.final_year):
                
        
        # get paid
        taxable_salary = my_employment.get_salary(year)
        # not putting this in cash, because I actually recieve this after the tax is taken

        
        # get UK gross interest
        gross_interest = my_fixed_interest.pay_interest() 
        
        nsi_interest = my_NSI.pay_interest()
        taxable_interest = hmrc.taxable_interest(taxable_income=taxable_salary, gross_interest=gross_interest)
        
        filipe.put_in_cash(nsi_interest)
        filipe.put_in_cash(gross_interest)

        # get UK dividends # TODO: tax dividends
        dividends = 200

        # INVESTMENT GROWTH
        my_ISA.grow_per_year()
        my_gia.grow_per_year()
        my_pension.grow_per_year()
    
             

        ## income into pension from salary ##
        total_pension_contributions =  my_employment.get_employee_pension_contributions(year) + \
             my_employment.get_employer_pension_contributions(year)
        my_pension.put_money(total_pension_contributions)


        # pension draw down (need to do this before tax because pension income is taxable)
        amount_to_take_from_pension_pot = filipe.pension_draw_down_function(pot_value=my_pension.asset_value,
                                                                                   current_year=year,
                                                                                   retirement_year=args.retirement_year,
                                                                                   final_year=args.final_year)
        taken_from_pension = my_pension.get_money(amount_to_take_from_pension_pot)
        #filipe.put_in_cash(taken_from_pension)

        ## Calculate TAXES ##
        if year == args.retirement_year:
            taxable_pension_income = 0
        else:
            taxable_pension_income = taken_from_pension
        # pension allowance
        pension_allowance = hmrc.pension_allowance(taxable_income_post_pension=taxable_salary + taxable_interest,
                                                   individual_pension_contribution=my_employment.get_employee_pension_contributions(year),
                                                   employer_contribution=my_employment.get_employer_pension_contributions(year))
        pension_pay_over_allowance = max(0, total_pension_contributions - pension_allowance)

        total_taxable_income = taxable_salary + taxable_interest + pension_pay_over_allowance + taxable_pension_income

        income_tax_due = hmrc.calculate_uk_income_tax(total_taxable_income)

        ni_due = hmrc.calculate_uk_national_insurance(taxable_salary+ my_employment.get_employee_pension_contributions(year))
               
        income_after_tax = taxable_salary + taken_from_pension - income_tax_due - ni_due
        
        # NOW I CAN PUT THIS IN CASH before paying things ##
        filipe.put_in_cash(income_after_tax)

        #### pay my living costs
        filipe.get_from_cash(filipe.living_costs[year])
        
        if year >= args.retirement_year:
            utility_income_multiplier = args.utility_income_multiplier_ret
            utility_investments_multiplier = args.utility_investments_multiplier_ret
            utility_pension_multiplier = args.utility_pension_multiplier_ret
        else:
            utility_income_multiplier = args.utility_income_multiplier_work
            utility_investments_multiplier = args.utility_investments_multiplier_work
            utility_pension_multiplier = args.utility_pension_multiplier_work


        utility_desired = max(args.utility_base, min(args.utility_cap, income_after_tax*utility_income_multiplier + \
                                                get_last_element_or_zero(pension_list)*utility_pension_multiplier + \
                                                (my_ISA.asset_value + my_gia.asset_value)*utility_investments_multiplier))
        #don't buy more utility than I have in assets and never more than utility_cap
        # I can't buy more utility than I have in ISA AND GIA combined and I don't want to buy more than 100k


        # CAPITAL GAINS (and accessing GIA if I need it for other reasons)
        desired_buffer_in_cash = (filipe.living_costs[year]*args.buffer_multiplier + get_last_element_or_zero(capital_gains_tax_list))
        
        amount_needed = max(desired_buffer_in_cash  + utility_desired - filipe.cash, 0)

        amount_needed_from_gia = min(my_gia.asset_value, amount_needed)
        amount_needed_from_elsewhere = max(0, amount_needed - amount_needed_from_gia)
        
        if amount_needed_from_elsewhere > 0:
            isa_money = my_ISA.get_money(amount=amount_needed_from_elsewhere)
            filipe.put_in_cash(isa_money)
        
        if amount_needed_from_gia <= 0:
            if args.CG_strategy == "harvest" and my_gia.asset_value > 1:
                gia_money, capital_gains = my_gia.get_money(my_gia.asset_value-1)
                my_gia.put_money(gia_money)
                capital_gains_tax = hmrc.capital_gains_tax_due(capital_gains)

            elif args.CG_strategy == "let_grow":
                capital_gains = 0
                capital_gains_tax = 0
        
        elif amount_needed_from_gia > 1:
            if args.CG_strategy == "harvest" and my_gia.asset_value > 1:
                gia_money, capital_gains = my_gia.get_money(my_gia.asset_value-1)
                my_gia.put_money(gia_money - amount_needed_from_gia)
                capital_gains_tax = hmrc.capital_gains_tax_due(capital_gains)

            elif args.CG_strategy == "let_grow":
                extra_cash, capital_gains = my_gia.get_money(amount_needed_from_gia)
                filipe.put_in_cash(extra_cash)
                capital_gains_tax = hmrc.capital_gains_tax_due(capital_gains)

        filipe.put_in_cash(amount_needed_from_gia)
        
        # I pay CGT next year
        
        
        ## AFTER I PAY TAXES AND LIVING EXPENSES, I INVEST OR BUY UTILITY ##
        filipe.buy_utility(min(utility_desired, filipe.cash))


        # INVEST FOR NEXT YEAR #
        money_for_ISA = filipe.get_from_cash(min(20000, max(filipe.cash - desired_buffer_in_cash, 0)))
        if money_for_ISA > 1:
            my_ISA.put_money(money_for_ISA)
        
        money_for_gia = filipe.get_from_cash(0.5*(max(0, filipe.cash - desired_buffer_in_cash)))
        if money_for_gia > 1:
            my_gia.put_money(money_for_gia)
        
        total_assets = my_pension.asset_value + my_ISA.asset_value + my_gia.asset_value + filipe.cash

        # LOG VALUES
        cash_list.append(filipe.cash)
        ammount_needed_from_gia_list.append(amount_needed_from_gia)
        pension_list.append(my_pension.asset_value)
        ISA_list.append(my_ISA.asset_value)
        GIA_list.append(my_gia.asset_value)
        all_tax_list.append(ni_due + income_tax_due + capital_gains_tax)
        capital_gains_list.append(capital_gains)
        capital_gains_tax_list.append(capital_gains_tax)
        taxable_salary_list.append(taxable_salary)
        gross_interest_list.append(gross_interest)
        taxable_interest_list.append(taxable_interest)
        pension_allowance_list.append(pension_allowance)
        pension_pay_over_allowance_list.append(pension_pay_over_allowance)
        taken_from_pension_list.append(taken_from_pension)
        total_taxable_income_list.append(total_taxable_income)
        income_tax_due_list.append(income_tax_due)
        national_insurance_due_list.append(ni_due)
        income_after_tax_list.append(income_after_tax)
        living_costs_list.append(filipe.living_costs[year])
        money_invested_in_ISA.append(money_for_ISA)
        money_invested_in_GIA.append(money_for_gia)
        TOTAL_ASSETS_list.append(total_assets)

    
    
    total_ut = round(sum(filipe.utility) + filipe.cash)
    df = pd.DataFrame({
        'Taxable Salary': taxable_salary_list,
        'Gross Interest': gross_interest_list,
        'Taxable Interest': taxable_interest_list,
        'Capital Gains': capital_gains_list,
        'Capital Gains Tax': capital_gains_tax_list,
        'Pension Allowance': pension_allowance_list,
        'Pension Pay Over Allowance': pension_pay_over_allowance_list,
        'Taken from Pension Pot': taken_from_pension_list,
        'Total Taxable Income': total_taxable_income_list,
        'Income Tax Due': income_tax_due_list,
        'National Insurance Due': national_insurance_due_list,
        'Total Tax': all_tax_list,
        'Amount Needed from GIA': ammount_needed_from_gia_list,
        'Living Costs': living_costs_list,
        'Income After Tax': income_after_tax_list,
        'Cash': cash_list,
        'Pension': pension_list,
        'ISA': ISA_list,
        'GIA': GIA_list,
        'Utility': filipe.utility,
        'Total Assets': TOTAL_ASSETS_list,
        'Money Invested in ISA': money_invested_in_ISA,
        'Money Invested in GIA': money_invested_in_GIA,
    }, index=range(args.start_year, args.final_year))

    print('TOTAL UTILITY ,' , total_ut)

    return total_ut, df