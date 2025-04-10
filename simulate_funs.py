# Import necessary classes and functions
from human import (Employment, Human, generate_living_costs, generate_salary,
                   linear_pension_draw_down_function, calculate_desired_utility)
from uk_gov import TaxMan
from investments_and_savings import PensionAccount, SotcksAndSharesISA, GeneralInvestmentAccount, FixedInterest
from aux_funs import get_last_element_or_zero

# Standard library imports
import logging
import argparse
import os
from datetime import datetime

# Third-party imports
import pandas as pd
import plotly.express as px
from google.cloud import storage
import numpy as np
import numpy_financial as npf

def simulate_a_life(args):
    """
    Runs the financial life simulation year by year.

    Args:
        args (argparse.Namespace): Parsed command-line arguments containing simulation parameters.

    Returns:
        tuple: (metric, df)
            metric (float): The calculated optimization metric (discounted utility penalized by volatility).
            df (pd.DataFrame): DataFrame containing the detailed simulation results per year.
    """

    # --- Initialization of Lists to Track Simulation Variables ---
    # (Tracking lists remain the same)
    taxable_salary_list = []
    gross_interest_list = []
    taxable_interest_list = []
    capital_gains_list = []
    capital_gains_tax_list = []
    pension_allowance_list = []
    pension_pay_over_allowance_list = []
    taken_from_pension_list = []
    taxable_pension_income_list = []
    total_taxable_income_list = []
    income_tax_due_list = []
    national_insurance_due_list = []
    all_tax_list = []
    income_after_tax_list = []
    cash_list = []
    pension_list = []
    ISA_list = []
    GIA_list = []
    fixed_interest_list = []
    nsi_list = []
    TOTAL_ASSETS_list = []
    invested_in_ISA_list = []
    invested_in_GIA_list = []
    taken_from_gia_list = []
    taken_from_isa_list = []
    living_costs_list = []
    utility_i_can_afford_list = []
    utility_desired_list = []
    actual_utility_value_list = []
    extra_cash_needed_to_pay_living_costs_list = []
    extra_cash_needed_all_list = []
    unpaid_living_costs_list = []
    extra_cash_needed_after_gia_list = []
    extra_cash_needed_after_gia_and_isa_list = []


    # --- Setup Simulation Entities ---
    filipe = Human(starting_cash=args.starting_cash,
                   living_costs=generate_living_costs(),
                   non_linear_utility=args.non_linear_utility,
                   pension_draw_down_function=linear_pension_draw_down_function)

    my_employment = Employment(gross_salary=generate_salary(),
                               employee_pension_contributions_pct=args.employee_pension_contributions_pct,
                               employer_pension_contributions_pct=args.employer_pension_contributions_pct)

    my_fixed_interest = FixedInterest(initial_value=args.fixed_interest_capital, interest_rate=args.fixed_interest_rate)
    my_NSI = FixedInterest(initial_value=args.NSI_capital, interest_rate=args.NSI_interest_rate)
    my_pension = PensionAccount(initial_value=args.pension_capital, growth_rate=args.pension_growth_rate)
    my_ISA = SotcksAndSharesISA(initial_value=args.ISA_capital, growth_rate=args.ISA_growth_rate)
    my_gia = GeneralInvestmentAccount(initial_value=args.GIA_capital,
                                      initial_units=args.GIA_initial_units,
                                      initial_average_buy_price=args.GIA_initial_average_buy_price,
                                      growth_rate=args.GIA_growth_rate)
    hmrc = TaxMan()


    # --- Simulation Loop ---
    for year in range(args.start_year, args.final_year + 1):

        # --- Calculate Desired Utility for the current year ---
        utility_desired = calculate_desired_utility(
            year=year,
            start_year=args.start_year,
            baseline=args.utility_baseline,
            linear_rate=args.utility_linear_rate,
            exp_rate=args.utility_exp_rate
        )

        # --- 1. Income Phase ---
        # Salary (after employee pension contributions, before tax)
        taxable_salary = my_employment.get_salary_before_tax_after_pension_contributions(year)

        # Interest Income (Gross)
        gross_interest = my_fixed_interest.pay_interest()
        nsi_interest = my_NSI.pay_interest() # NSI interest is tax-free

        # Add gross interest amounts to cash (tax calculated later)
        filipe.put_in_cash(nsi_interest)
        filipe.put_in_cash(gross_interest)

        # Dividends (Placeholder)
        dividends = 0

        # --- 2. Investment Growth Phase ---
        my_ISA.grow_per_year()
        my_gia.grow_per_year()
        my_pension.grow_per_year()

        # --- 3. Pension Contributions & Drawdown Phase ---
        # Contributions
        employee_contrib = my_employment.get_employee_pension_contributions(year)
        employer_contrib = my_employment.get_employer_pension_contributions(year)
        total_pension_contributions = employee_contrib + employer_contrib
        my_pension.put_money(total_pension_contributions)

        # Drawdown
        to_take_from_pension_pot = filipe.pension_draw_down_function(
            pot_value=my_pension.asset_value,
            current_year=year,
            retirement_year=args.retirement_year,
            final_year=args.final_year
        )
        taken_from_pension = my_pension.get_money(to_take_from_pension_pot)

        # --- Determine Taxable Pension Income (Moved earlier for PSA calculation) ---
        if year == args.retirement_year:
            # Assuming the entire 'taken_from_pension' in retirement year is the tax-free lump sum
            taxable_pension_income = 0
            # Add the tax-free lump sum directly to cash
            filipe.put_in_cash(taken_from_pension)
        elif year > args.retirement_year:
            taxable_pension_income = taken_from_pension
            # Taxable pension income added to cash later (after tax calculation)
        else:
            taxable_pension_income = 0 # No pension income before retirement


        # --- Calculate Taxable Interest (using improved income estimate) ---
        # Estimate income for determining Personal Savings Allowance (PSA) tax band.
        # Includes salary, gross interest (as it contributes to the band), and taxable pension income.
        # Excludes pension allowance charge for simplicity (as it depends on final income).
        income_estimate_for_psa = taxable_salary + gross_interest + taxable_pension_income
        taxable_interest = hmrc.taxable_interest(
            taxable_income=income_estimate_for_psa, # Use the improved estimate
            gross_interest=gross_interest
        )

        # --- 4. Tax Calculation Phase ---
        # Calculate Pension Allowance & Potential Tax Charge
        # Note: Income definition for allowance check still uses taxable_salary + taxable_interest
        # This could be refined further but adds complexity.
        income_for_allowance_check = taxable_salary + taxable_interest # Using taxable interest here
        pension_allowance = hmrc.pension_allowance(
            taxable_income_post_pension=income_for_allowance_check,
            individual_pension_contribution=employee_contrib,
            employer_contribution=employer_contrib
        )
        pension_pay_over_allowance = max(0, total_pension_contributions - pension_allowance)

        # Calculate Total Taxable Income (using the calculated taxable_interest)
        total_taxable_income = (taxable_salary
                                + taxable_interest # Use the calculated taxable amount
                                + pension_pay_over_allowance
                                + taxable_pension_income
                                + dividends)

        # Calculate Income Tax
        income_tax_due = hmrc.calculate_uk_income_tax(total_taxable_income)

        # Calculate National Insurance
        gross_salary_for_ni = my_employment.get_gross_salary(year)
        ni_due = hmrc.calculate_uk_national_insurance(gross_salary_for_ni)

        # Calculate Net Income to Add to Cash
        income_after_tax = (taxable_salary
                            + taxable_pension_income # Add taxable pension income here
                            - income_tax_due
                            - ni_due)
        # Add the net income to cash (NSI interest & gross fixed interest already added)
        # Tax-free lump sum also already added if applicable.
        filipe.put_in_cash(income_after_tax)

        # --- 5. Spending Phase (Living Costs & Utility) ---
        # (Logic remains the same)
        living_costs = filipe.living_costs.get(year, 0)
        cash_available = filipe.cash
        if living_costs <= cash_available:
            paid_living_costs = filipe.get_from_cash(living_costs)
            extra_cash_needed_to_pay_living_costs = 0
            unpaid_living_costs = 0
        else:
            paid_living_costs = filipe.get_from_cash(max(0, cash_available - 1))
            extra_cash_needed_to_pay_living_costs = living_costs - paid_living_costs
            unpaid_living_costs = extra_cash_needed_to_pay_living_costs

        # --- 6. Funding Shortfalls & Buffer Phase (Using Investments) ---
        # (Logic remains the same)
        buffer_amount = args.buffer_multiplier * living_costs
        extra_cash_needed_all = (extra_cash_needed_to_pay_living_costs
                                 + utility_desired
                                 + buffer_amount)
        capital_gains = 0
        capital_gains_tax = 0
        gia_extract_net = 0
        amount_taken_from_gia = 0
        if extra_cash_needed_all > 0 and my_gia.asset_value > 0:
            estimated_gia_needed_gross = extra_cash_needed_all * (1 + hmrc.capital_gains_tax_rate)
            amount_to_attempt_gia = min(my_gia.asset_value, estimated_gia_needed_gross)
            result = my_gia.get_money(amount_to_attempt_gia)
            if isinstance(result, tuple):
                amount_taken_from_gia, capital_gains = result
                capital_gains_tax = hmrc.capital_gains_tax_due(capital_gains)
                gia_extract_net = amount_taken_from_gia - capital_gains_tax
                filipe.put_in_cash(gia_extract_net)
            else:
                 amount_taken_from_gia = 0; capital_gains = 0; capital_gains_tax = 0; gia_extract_net = 0
        else:
            amount_taken_from_gia = 0

        extra_cash_needed_after_gia = max(0, extra_cash_needed_all - gia_extract_net)
        amount_taken_from_isa = 0
        if extra_cash_needed_after_gia > 0 and my_ISA.asset_value > 0:
            amount_to_attempt_isa = min(my_ISA.asset_value, extra_cash_needed_after_gia)
            amount_taken_from_isa = my_ISA.get_money(amount=amount_to_attempt_isa)
            filipe.put_in_cash(amount_taken_from_isa)
        else:
            amount_taken_from_isa = 0
        extra_cash_needed_after_gia_and_isa = max(0, extra_cash_needed_after_gia - amount_taken_from_isa)

        # --- 7. Final Spending & Utility Calculation ---
        # (Logic remains the same)
        if unpaid_living_costs > 0:
             can_pay_now = min(unpaid_living_costs, filipe.cash)
             if can_pay_now > 0:
                 _ = filipe.get_from_cash(can_pay_now)
                 unpaid_living_costs -= can_pay_now
        cash_available_for_utility = max(0, filipe.cash - buffer_amount)
        utility_i_can_afford = min(cash_available_for_utility, utility_desired)
        if utility_i_can_afford > 0:
             filipe.buy_utility(utility_i_can_afford)
             actual_utility_value = utility_i_can_afford ** filipe.non_linear_utility
        else:
             if unpaid_living_costs > 0:
                 utility_penalty = -(unpaid_living_costs**2)
                 filipe.utility.append(utility_penalty)
                 actual_utility_value = utility_penalty
                 utility_i_can_afford = utility_penalty
             else:
                 filipe.utility.append(0)
                 actual_utility_value = 0

        # --- 8. Investment Phase (Surplus Cash) ---
        # (Logic remains the same)
        cash_above_buffer = max(0, filipe.cash - buffer_amount)
        invested_in_ISA_this_year = 0
        invested_in_GIA_this_year = 0
        isa_allowance_remaining = 20000
        if cash_above_buffer > 0 and isa_allowance_remaining > 0:
            money_for_ISA = min(cash_above_buffer, isa_allowance_remaining)
            actual_isa_investment = filipe.get_from_cash(money_for_ISA)
            if actual_isa_investment > 0:
                 my_ISA.put_money(actual_isa_investment)
                 invested_in_ISA_this_year = actual_isa_investment
                 cash_above_buffer -= actual_isa_investment
        if cash_above_buffer > 0:
             actual_gia_investment = filipe.get_from_cash(cash_above_buffer)
             if actual_gia_investment > 0:
                 my_gia.put_money(actual_gia_investment)
                 invested_in_GIA_this_year = actual_gia_investment

        # --- 9. Logging Phase (End of Year State) ---
        # (Logic remains the same)
        total_assets = my_pension.asset_value + my_ISA.asset_value + my_gia.asset_value + filipe.cash + my_fixed_interest.asset_value + my_NSI.asset_value
        cash_list.append(filipe.cash)
        pension_list.append(my_pension.asset_value)
        ISA_list.append(my_ISA.asset_value)
        GIA_list.append(my_gia.asset_value)
        fixed_interest_list.append(my_fixed_interest.asset_value)
        nsi_list.append(my_NSI.asset_value)
        TOTAL_ASSETS_list.append(total_assets)
        taxable_salary_list.append(taxable_salary)
        gross_interest_list.append(gross_interest + nsi_interest) # Log total gross interest
        taxable_interest_list.append(taxable_interest) # Log taxable amount after PSA
        capital_gains_list.append(capital_gains)
        capital_gains_tax_list.append(capital_gains_tax)
        pension_allowance_list.append(pension_allowance)
        pension_pay_over_allowance_list.append(pension_pay_over_allowance)
        taken_from_pension_list.append(taken_from_pension)
        taxable_pension_income_list.append(taxable_pension_income)
        total_taxable_income_list.append(total_taxable_income)
        income_tax_due_list.append(income_tax_due)
        national_insurance_due_list.append(ni_due)
        all_tax_list.append(ni_due + income_tax_due + capital_gains_tax)
        # Recalculate net cash inflow for logging clarity
        net_cash_inflow = (taxable_salary + taxable_pension_income - income_tax_due - ni_due
                          + nsi_interest + gross_interest # Add gross interest back (tax is part of income_tax_due)
                          + (taken_from_pension if year == args.retirement_year else 0)) # Add lump sum
        income_after_tax_list.append(net_cash_inflow) # Log net cash inflow more accurately

        living_costs_list.append(living_costs)
        utility_i_can_afford_list.append(utility_i_can_afford)
        utility_desired_list.append(utility_desired)
        actual_utility_value_list.append(actual_utility_value)
        invested_in_ISA_list.append(invested_in_ISA_this_year)
        invested_in_GIA_list.append(invested_in_GIA_this_year)
        taken_from_gia_list.append(amount_taken_from_gia)
        taken_from_isa_list.append(amount_taken_from_isa)
        extra_cash_needed_to_pay_living_costs_list.append(extra_cash_needed_to_pay_living_costs)
        extra_cash_needed_all_list.append(extra_cash_needed_all)
        unpaid_living_costs_list.append(unpaid_living_costs)
        extra_cash_needed_after_gia_list.append(extra_cash_needed_after_gia)
        extra_cash_needed_after_gia_and_isa_list.append(extra_cash_needed_after_gia_and_isa)


    # --- Post-Simulation Analysis ---
    # (Logic remains the same)
    final_utility_values = filipe.utility
    if not final_utility_values:
         print("Warning: No utility values recorded during simulation.")
         total_ut, var_ut, std_ut, mean_ut, sigma_ut, discounted_utility = 0, 0, 0, 0, 0, 0
         metric = -float('inf')
    else:
        total_ut = round(sum(final_utility_values))
        var_ut = np.var(final_utility_values)
        std_ut = np.std(final_utility_values)
        mean_ut = np.mean(final_utility_values)
        sigma_ut = abs(std_ut / mean_ut) if abs(mean_ut) > 1e-6 else 0
        discounted_utility = npf.npv(args.utility_discount_rate, final_utility_values).round(0)
        metric = discounted_utility - args.volatility_penalty * sigma_ut


    # --- Create Results DataFrame ---
    # (DataFrame creation remains the same)
    df = pd.DataFrame({
        # Assets
        'Cash': cash_list, 'Pension': pension_list, 'ISA': ISA_list, 'GIA': GIA_list,
        'Fixed Interest': fixed_interest_list, 'NSI': nsi_list, 'Total Assets': TOTAL_ASSETS_list,
        # Income
        'Taxable Salary': taxable_salary_list, 'Gross Interest': gross_interest_list,
        'Taxable Interest': taxable_interest_list, 'Taken from Pension Pot': taken_from_pension_list,
        'Taxable Pension Income': taxable_pension_income_list, 'Income After Tax': income_after_tax_list,
        # Taxes & Gains
        'Capital Gains': capital_gains_list, 'Capital Gains Tax': capital_gains_tax_list,
        'Pension Allowance': pension_allowance_list, 'Pension Pay Over Allowance': pension_pay_over_allowance_list,
        'Total Taxable Income': total_taxable_income_list, 'Income Tax Due': income_tax_due_list,
        'National Insurance Due': national_insurance_due_list, 'Total Tax': all_tax_list,
        # Spending & Utility
        'Living Costs': living_costs_list, 'Utility Desired': utility_desired_list,
        'Utility Affordable': utility_i_can_afford_list, 'Utility Value': actual_utility_value_list,
        'Unpaid Living Costs': unpaid_living_costs_list,
        # Investments & Withdrawals
        'Money Invested in ISA': invested_in_ISA_list, 'Money Invested in GIA': invested_in_GIA_list,
        'Amount taken from GIA': taken_from_gia_list, 'Amount taken from ISA': taken_from_isa_list,
        # Cash Flow Analysis (Optional)
        #'Cash Needed Living Costs': extra_cash_needed_to_pay_living_costs_list,
        #'Cash Needed All': extra_cash_needed_all_list,
        #'Cash Needed After GIA': extra_cash_needed_after_gia_list,
        #'Cash Needed After ISA': extra_cash_needed_after_gia_and_isa_list,

    }, index=range(args.start_year, args.final_year + 1))

    # --- Print Summary Metrics ---
    # (Summary printing remains the same)
    print(f"--- Simulation Summary ---")
    print(f"Total Raw Utility: {total_ut}")
    print(f"Mean Utility: {mean_ut:.2f}")
    print(f"Utility StDev: {std_ut:.2f}")
    print(f"Utility Sigma (StDev/Mean): {sigma_ut:.4f}")
    print(f"Discounted Utility (Rate={args.utility_discount_rate:.2%}): {discounted_utility}")
    print(f"Volatility Penalty Factor: {args.volatility_penalty}")
    print(f"Final Metric (Discounted Utility - Penalty*Sigma): {metric:.2f}")
    print(f"Final Total Assets ({args.final_year}): {TOTAL_ASSETS_list[-1]:,.0f}")
    print(f"--- End Summary --- \n")


    return metric, df
