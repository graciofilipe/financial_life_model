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
import numpy as np


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
    pension_list = []
    ISA_list = []
    GIA_list = [] 
    living_costs_list = []
    taken_from_gia_list = []
    TOTAL_ASSETS_list = []
    invested_in_ISA_list = []
    invested_in_GIA_list = []
    utility_i_can_afford_list = []
    utility_desired_list = []
    extra_cash_needed_to_pay_living_costs_list = []
    extra_cash_needed_all_list = []
    unpaid_living_costs_list = []
    to_take_from_gia_list = []
    extra_cash_needed_after_gia_list = []
    to_take_from_ISA_list = []
    extra_cash_needed_after_gia_and_isa_list = []
    


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
                   non_linear_utility=args.non_linear_utility,
                   pension_draw_down_function=linear_pension_draw_down_function)
    
    utility_dict = {2024: int(args.utility_2024_2029),
                2025: int(args.utility_2024_2029),
                2026: int(args.utility_2024_2029),
                2027: int(args.utility_2024_2029),
                2028: int(args.utility_2024_2029),
                2029: int(args.utility_2024_2029),
                2030: int(args.utility_2030_2034),
                2031: int(args.utility_2030_2034),
                2032: int(args.utility_2030_2034),
                2033: int(args.utility_2030_2034),
                2034: int(args.utility_2030_2034),
                2035: int(args.utility_2035_2039),
                2036: int(args.utility_2035_2039),
                2037: int(args.utility_2035_2039),
                2038: int(args.utility_2035_2039),
                2039: int(args.utility_2035_2039),
                2040: int(args.utility_2040_2044),
                2041: int(args.utility_2040_2044),
                2042: int(args.utility_2040_2044),
                2043: int(args.utility_2040_2044),
                2044: int(args.utility_2040_2044),
                2045: int(args.utility_2045_2049),
                2046: int(args.utility_2045_2049),
                2047: int(args.utility_2045_2049),
                2048: int(args.utility_2045_2049),
                2049: int(args.utility_2045_2049),
                2050: int(args.utility_2050_2054),
                2051: int(args.utility_2050_2054),
                2052: int(args.utility_2050_2054),
                2053: int(args.utility_2050_2054),
                2054: int(args.utility_2050_2054),
                2055: int(args.utility_2055_2059),
                2056: int(args.utility_2055_2059),
                2057: int(args.utility_2055_2059),
                2058: int(args.utility_2055_2059),
                2059: int(args.utility_2055_2059),
                2060: int(args.utility_2060_2064),
                2061: int(args.utility_2060_2064),
                2062: int(args.utility_2060_2064),
                2063: int(args.utility_2060_2064),
                2064: int(args.utility_2060_2064),
                2065: int(args.utility_2065_2069),
                2066: int(args.utility_2065_2069),
                2067: int(args.utility_2065_2069),
                2068: int(args.utility_2065_2069),
                2069: int(args.utility_2065_2069),
                2070: int(args.utility_2070_2074),
                2071: int(args.utility_2070_2074),
                2072: int(args.utility_2070_2074),
                2073: int(args.utility_2070_2074),
                2074: int(args.utility_2070_2074)
                }

    hmrc = TaxMan()
    
    for year in range(args.start_year, args.final_year):
                
        
        # get paid
        taxable_salary = my_employment.get_salary_before_tax_after_pension_contributions(year)
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
        to_take_from_pension_pot = filipe.pension_draw_down_function(pot_value=my_pension.asset_value,
                                                                            current_year=year,
                                                                            retirement_year=args.retirement_year,
                                                                            final_year=args.final_year)
        taken_from_pension = my_pension.get_money(to_take_from_pension_pot)

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
        living_costs = filipe.living_costs[year]
        if living_costs < filipe.cash:
            _ = filipe.get_from_cash(filipe.living_costs[year])
            extra_cash_needed_to_pay_living_costs = 0 
        else:
            taken = filipe.get_from_cash(filipe.cash - 1) #leave myself $1
            extra_cash_needed_to_pay_living_costs = living_costs - taken
        

        # # Now deal with Utility (I have to deal with this now so I know how much I need to take from GIA) 
        # if year >= args.retirement_year:
        #     utility_income_multiplier = args.utility_income_multiplier_ret
        #     utility_investments_multiplier = args.utility_investments_multiplier_ret
        #     utility_pension_multiplier = args.utility_pension_multiplier_ret
        # else:
        #     utility_income_multiplier = args.utility_income_multiplier_work
        #     utility_investments_multiplier = args.utility_investments_multiplier_work
        #     utility_pension_multiplier = args.utility_pension_multiplier_work


        # utility_desired = max(args.utility_base, min(args.utility_cap, income_after_tax*utility_income_multiplier + \
        #                                              get_last_element_or_zero(pension_list)*utility_pension_multiplier + \
        #                                             (my_ISA.asset_value + my_gia.asset_value)*utility_investments_multiplier + \
        #                                              args.utility_total_assets_years_left_multiplier*(args.final_year - year)*get_last_element_or_zero(TOTAL_ASSETS_list)))

        utility_desired = utility_dict[year]
        
        #don't buy more utility than I have in assets and never more than utility_cap
        # I can't buy more utility than I have in ISA AND GIA combined and I don't want to buy more than 100k


        # CAPITAL GAINS (and accessing GIA if I need it for other reasons)
        extra_cash_needed_all = max(0,
            args.buffer_multiplier*filipe.living_costs[year] + \
            utility_desired + \
            extra_cash_needed_to_pay_living_costs + \
            get_last_element_or_zero(capital_gains_tax_list)
            )

        to_take_from_gia = min(my_gia.asset_value, extra_cash_needed_all)

        #HARVEST (and leave some out if needed)
        taken_from_gia, capital_gains = my_gia.get_money(my_gia.asset_value)
        my_gia.put_money(taken_from_gia - to_take_from_gia)
        capital_gains_tax = hmrc.capital_gains_tax_due(capital_gains)
        filipe.put_in_cash(to_take_from_gia)


        extra_cash_needed_after_gia = max(0, extra_cash_needed_all - to_take_from_gia)
        if extra_cash_needed_after_gia > 0:
            to_take_from_ISA = min(my_ISA.asset_value, extra_cash_needed_after_gia)
            taken_from_isa = my_ISA.get_money(amount=to_take_from_ISA)
            filipe.put_in_cash(taken_from_isa)
            extra_cash_needed_after_gia_and_isa = extra_cash_needed_after_gia - taken_from_isa
        else:
            extra_cash_needed_after_gia_and_isa = 0
            to_take_from_ISA = 0



        # PAY THE REMAINING LIVING COSTS
        if filipe.cash >  extra_cash_needed_to_pay_living_costs:
            _ = filipe.get_from_cash(extra_cash_needed_to_pay_living_costs)
            unpaid_living_costs = 0
        else:
            payed_living_costs = filipe.get_from_cash(filipe.cash-1)
            unpaid_living_costs = extra_cash_needed_to_pay_living_costs - payed_living_costs
                
        
        ## AFTER I PAY TAXES AND LIVING EXPENSES, I INVEST OR BUY UTILITY ##
        # I couldn't find the following money so I need to take it from the utility desired

        if unpaid_living_costs > 0:
            filipe.utility.append(-(unpaid_living_costs)**2) # exp penalty for negative utility
            utility_i_can_afford = - unpaid_living_costs
        else:
            #utility_i_can_afford = max(0, utility_desired - extra_cash_needed_after_gia_and_isa - extra_cash_needed_to_pay_living_costs)
            utility_i_can_afford = min(filipe.cash, utility_desired)
            filipe.buy_utility(utility_i_can_afford)


        # INVEST FOR NEXT YEAR #
        available = max(0, filipe.cash - args.buffer_multiplier*filipe.living_costs[year])

        money_for_ISA = filipe.get_from_cash(min(20000, available))
        if money_for_ISA > 1:
            my_ISA.put_money(money_for_ISA)
            available = max(0, available - money_for_ISA)
        
        money_for_gia = filipe.get_from_cash(available)
        if money_for_gia > 1:
            my_gia.put_money(money_for_gia)
        
        total_assets = my_pension.asset_value + my_ISA.asset_value + my_gia.asset_value + filipe.cash

        # LOG VALUES
        cash_list.append(filipe.cash)
        taken_from_gia_list.append(taken_from_gia)
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
        invested_in_ISA_list.append(money_for_ISA)
        invested_in_GIA_list.append(money_for_gia)
        utility_i_can_afford_list.append(utility_i_can_afford)
        utility_desired_list.append(utility_desired)
        extra_cash_needed_to_pay_living_costs_list.append(extra_cash_needed_to_pay_living_costs)
        extra_cash_needed_all_list.append(extra_cash_needed_all)
        TOTAL_ASSETS_list.append(total_assets)
        to_take_from_gia_list.append(to_take_from_gia)
        extra_cash_needed_after_gia_list.append(extra_cash_needed_after_gia)
        to_take_from_ISA_list.append(to_take_from_ISA)
        extra_cash_needed_after_gia_and_isa_list.append(extra_cash_needed_after_gia_and_isa)
        unpaid_living_costs_list.append(unpaid_living_costs)


    total_ut = round(sum(filipe.utility))
    var_ut = np.var(filipe.utility)
    std_ut = np.std(filipe.utility)
    mean_ut = np.mean(filipe.utility)
    sigma_ut = abs(std_ut/mean_ut)
    import numpy_financial as npf
    discounted_utility = npf.npv(args.utility_discount_rate, filipe.utility).round(0)

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
        'Amount taken from GIA': taken_from_gia_list,
        'Living Costs': living_costs_list,
        'Income After Tax': income_after_tax_list,
        'Cash': cash_list,
        'Pension': pension_list,
        'ISA': ISA_list,
        'GIA': GIA_list,
        'Utility I can afford': utility_i_can_afford_list,
        'Utility Desired': utility_desired_list,
        'Utility': filipe.utility,
        'Total Assets': TOTAL_ASSETS_list,
        'Money Invested in ISA': invested_in_ISA_list,
        'Money Invested in GIA': invested_in_GIA_list,
        'Extra Cash Needed to Pay Living Costs': extra_cash_needed_to_pay_living_costs_list,
        'Extra Cash Needed All': extra_cash_needed_all_list,
        'Unpaid Living Costs': unpaid_living_costs_list,
        'To Take from GIA': to_take_from_gia_list,
        'Extra Cash Needed After GIA': extra_cash_needed_after_gia_list,
        'To Take from ISA': to_take_from_ISA_list,
        'Extra Cash Needed After GIA and ISA': extra_cash_needed_after_gia_and_isa_list,
        'Unpaid Living Costs': unpaid_living_costs_list,

    }, index=range(args.start_year, args.final_year))

    metric = discounted_utility - 100000*sigma_ut
    
    print('TOTAL UTILITY ,' , total_ut)
    print('Discounted UTILITY ,' , discounted_utility)
    print('sigma,' , sigma_ut)
    print('metric ', metric)
    print('\n')
    

    return metric, df