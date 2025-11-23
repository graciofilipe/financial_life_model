# Import necessary classes and functions
from .human import (Employment, Human, generate_living_costs, generate_salary,
                   linear_pension_draw_down_function, calculate_desired_utility)
from .uk_gov import TaxMan
from .investments_and_savings import PensionAccount, StocksAndSharesISA, GeneralInvestmentAccount, FixedInterest
from .aux_funs import get_last_element_or_zero

# Standard library imports
import logging
import argparse
import os
from datetime import datetime
import math # For assertions

# Third-party imports
import pandas as pd
import plotly.express as px
from google.cloud import storage
import numpy as np
import numpy_financial as npf

# Helper function for structured debug logging
def log_debug_event(debug_data_list, year, step_name, variable, value, context=""):
    """Appends a structured debug event to the debug data list."""
    event = {
        'Year': year,
        'Step': step_name,
        'Variable': variable,
        'Value': f"{value:.2f}" if isinstance(value, (int, float)) else value, # Format numbers
        'Context': context
    }
    debug_data_list.append(event)
    # Also log to standard logger at DEBUG level
    logging.debug(f"Year {year} | Step: {step_name} | Var: {variable} | Val: {event['Value']} | Context: {context}")


def calculate_taxes(year, args, hmrc, my_employment, taxable_salary, gross_interest, taxable_pension_income, employee_contrib, employer_contrib, total_pension_contributions, dividends=0, debug_data=None):
    """
    Calculates all tax liabilities and net income for the year.
    
    Returns:
        dict: Containing calculated tax values (taxable_interest, pension_allowance, 
              total_taxable_income, income_tax, ni, net_income).
    """
    step = "4. Tax Calculation"
    
    # State Pension
    state_pension_income = args.state_pension_amount if year >= args.state_pension_start_year else 0
    if debug_data is not None:
        log_debug_event(debug_data, year, step, "State Pension Income", state_pension_income)

    # Taxable Interest
    income_estimate_for_psa = taxable_salary + gross_interest + taxable_pension_income
    taxable_interest = hmrc.taxable_interest(
        taxable_income=income_estimate_for_psa, gross_interest=gross_interest
    )
    if debug_data is not None:
        log_debug_event(debug_data, year, step, "Taxable Interest (After PSA)", taxable_interest)

    # Pension Allowance
    income_for_allowance_check = taxable_salary + taxable_interest + state_pension_income
    pension_allowance = hmrc.pension_allowance(
        taxable_income_post_pension=income_for_allowance_check,
        individual_pension_contribution=employee_contrib,
        employer_contribution=employer_contrib
    )
    if debug_data is not None:
        log_debug_event(debug_data, year, step, "Pension Annual Allowance", pension_allowance)
        
    pension_pay_over_allowance = max(0, total_pension_contributions - pension_allowance)
    if debug_data is not None:
        log_debug_event(debug_data, year, step, "Pension Contributions Over Allowance", pension_pay_over_allowance)

    # Total Taxable Income
    total_taxable_income = (taxable_salary + taxable_interest + pension_pay_over_allowance
                            + taxable_pension_income + dividends + state_pension_income)
    if debug_data is not None:
        log_debug_event(debug_data, year, step, "Total Taxable Income", total_taxable_income)

    # Income Tax
    income_tax_due = hmrc.calculate_uk_income_tax(total_taxable_income)
    if debug_data is not None:
        log_debug_event(debug_data, year, step, "Income Tax Due", income_tax_due)
    assert income_tax_due >= 0, f"Year {year}: Negative Income Tax ({income_tax_due})"

    # National Insurance
    gross_salary_for_ni = my_employment.get_gross_salary(year)
    ni_due = hmrc.calculate_uk_national_insurance(gross_salary_for_ni)
    if debug_data is not None:
        log_debug_event(debug_data, year, step, "National Insurance Due", ni_due)
    assert ni_due >= 0, f"Year {year}: Negative NI ({ni_due})"

    # Net Income
    income_after_tax = (taxable_salary + taxable_pension_income + state_pension_income - income_tax_due - ni_due)
    if debug_data is not None:
        log_debug_event(debug_data, year, step, "Net Income (Salary+Pension+State-Tax-NI)", income_after_tax)

    return {
        "taxable_interest": taxable_interest,
        "pension_allowance": pension_allowance,
        "pension_pay_over_allowance": pension_pay_over_allowance,
        "total_taxable_income": total_taxable_income,
        "income_tax_due": income_tax_due,
        "ni_due": ni_due,
        "state_pension_income": state_pension_income,
        "income_after_tax": income_after_tax
    }


def simulate_a_life(args):
    """
    Runs the financial life simulation year by year with detailed logging and assertions.

    Args:
        args (argparse.Namespace): Parsed command-line arguments containing simulation parameters.

    Returns:
        tuple: (metric, df, debug_data)
            metric (float): The calculated optimization metric.
            df (pd.DataFrame): DataFrame containing the main simulation results per year.
            debug_data (list): List of dictionaries containing detailed debug events.
    """
    logging.info("Initializing simulation...")

    # --- Initialization of Lists for Main Results ---
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
    unpaid_living_costs_list = []


    # --- Initialize List for Detailed Debug Data ---
    debug_data = []

    # --- PCLS (Lump Sum) State ---
    pcls_annual_amount = 0
    pcls_years_remaining = 0
    lump_sum_cap = 268275


    # --- Setup Simulation Entities ---
    try:
        # Ensure one_off_expenses exists in args, default to empty dict if not
        one_off_expenses = getattr(args, 'one_off_expenses', {})

        filipe = Human(starting_cash=args.starting_cash,
                       living_costs=generate_living_costs(base_cost=args.base_living_cost,
                                                          base_year=args.start_year,
                                                          rate_pre_retirement=args.living_costs_rate_pre_retirement,
                                                          rate_post_retirement=args.living_costs_rate_post_retirement,
                                                          retirement_year=args.retirement_year,
                                                          final_year=args.final_year,
                                                          one_off_expenses=one_off_expenses,
                                                          slow_down_year=args.slow_down_year,
                                                          rate_post_slow_down=args.living_costs_rate_post_slow_down),
                       non_linear_utility=args.non_linear_utility,
                       pension_draw_down_function=linear_pension_draw_down_function)
        log_debug_event(debug_data, args.start_year -1, "Init", "Start Cash", args.starting_cash)

        my_employment = Employment(gross_salary=generate_salary(base_salary=args.base_salary,
                                                                 base_year=args.start_year - 1,
                                                                 growth_rate=args.salary_growth_rate,
                                                                last_work_year=args.retirement_year - 1,
                                                                growth_stop_year=args.salary_growth_stop_year,
                                                                post_plateau_growth_rate=args.salary_post_plateau_growth_rate),
                                   employee_pension_contributions_pct=args.employee_pension_contributions_pct,
                                   employer_pension_contributions_pct=args.employer_pension_contributions_pct)

        my_fixed_interest = FixedInterest(initial_value=args.fixed_interest_capital, interest_rate=args.fixed_interest_rate)
        log_debug_event(debug_data, args.start_year -1, "Init", "Start Fixed Interest", args.fixed_interest_capital)
        my_NSI = FixedInterest(initial_value=args.NSI_capital, interest_rate=args.NSI_interest_rate)
        log_debug_event(debug_data, args.start_year -1, "Init", "Start NSI", args.NSI_capital)
        my_pension = PensionAccount(initial_value=args.pension_capital, growth_rate=args.pension_growth_rate)
        log_debug_event(debug_data, args.start_year -1, "Init", "Start Pension", args.pension_capital)
        my_ISA = StocksAndSharesISA(initial_value=args.ISA_capital, growth_rate=args.ISA_growth_rate)
        log_debug_event(debug_data, args.start_year -1, "Init", "Start ISA", args.ISA_capital)
        my_gia = GeneralInvestmentAccount(initial_value=args.GIA_capital,
                                          initial_units=args.GIA_initial_units,
                                          initial_average_buy_price=args.GIA_initial_average_buy_price,
                                          growth_rate=args.GIA_growth_rate)
        log_debug_event(debug_data, args.start_year -1, "Init", "Start GIA Value", args.GIA_capital)
        log_debug_event(debug_data, args.start_year -1, "Init", "Start GIA Units", args.GIA_initial_units)
        log_debug_event(debug_data, args.start_year -1, "Init", "Start GIA Avg Price", args.GIA_initial_average_buy_price)

        hmrc = TaxMan()
        logging.info("Simulation entities initialized successfully.")
    except Exception as e:
         logging.critical(f"Error during simulation entity initialization: {e}", exc_info=True)
         raise # Re-raise exception to halt execution


    # --- Simulation Loop ---
    logging.info(f"Starting simulation loop from {args.start_year} to {args.final_year}")
    for year in range(args.start_year, args.final_year + 1):
        logging.info(f"--- Processing Year {year} ---")

        # --- Stress Test: Market Crash Event ---
        if year == args.retirement_year and args.stress_test_market_crash_pct > 0:
            crash_factor = 1 - args.stress_test_market_crash_pct
            log_debug_event(debug_data, year, "Stress Test", "Market Crash Initiated", f"-{args.stress_test_market_crash_pct*100}%")
            
            # Apply to volatile assets
            my_pension.asset_value *= crash_factor
            my_ISA.asset_value *= crash_factor
            my_gia.asset_value *= crash_factor
            # GIA unit price also drops? Or just value?
            # If value drops, price drops.
            my_gia.current_unit_price *= crash_factor
            
            log_debug_event(debug_data, year, "Stress Test", "Pension Value Post-Crash", my_pension.asset_value)
            log_debug_event(debug_data, year, "Stress Test", "ISA Value Post-Crash", my_ISA.asset_value)
            log_debug_event(debug_data, year, "Stress Test", "GIA Value Post-Crash", my_gia.asset_value)


        # --- Calculate Desired Utility ---
        step = "0. Utility Calc"
        utility_desired = calculate_desired_utility(
            year=year,
            start_year=args.start_year,
            baseline=args.utility_baseline,
            linear_rate=args.utility_linear_rate,
            exp_rate=args.utility_exp_rate
        )
        log_debug_event(debug_data, year, step, "Utility Desired", utility_desired, f"Baseline={args.utility_baseline}, LinRate={args.utility_linear_rate}, ExpRate={args.utility_exp_rate}")

        # --- 1. Income Phase ---
        step = "1. Income"
        taxable_salary = my_employment.get_salary_before_tax_after_pension_contributions(year)
        log_debug_event(debug_data, year, step, "Taxable Salary (pre-tax, post-empl-pension)", taxable_salary)

        gross_interest = my_fixed_interest.pay_interest()
        log_debug_event(debug_data, year, step, "Gross Interest (Fixed)", gross_interest)
        nsi_interest = my_NSI.pay_interest()
        log_debug_event(debug_data, year, step, "Gross Interest (NSI)", nsi_interest)

        filipe.put_in_cash(nsi_interest)
        log_debug_event(debug_data, year, step, "Cash Add (NSI Interest)", nsi_interest)
        filipe.put_in_cash(gross_interest)
        log_debug_event(debug_data, year, step, "Cash Add (Gross Fixed Interest)", gross_interest)

        dividends = 0 # Placeholder
        log_debug_event(debug_data, year, step, "Dividends (Gross)", dividends)

        # --- 2. Investment Growth Phase ---
        step = "2. Growth"
        
        # Determine growth rates for this year
        # If a Monte Carlo map is provided, use the rate for this specific year.
        # Otherwise, pass None to use the account's internal default rate.
        current_year_market_rate = None
        if hasattr(args, 'market_returns_map') and args.market_returns_map and year in args.market_returns_map:
            current_year_market_rate = args.market_returns_map[year]
            log_debug_event(debug_data, year, step, "Market Return Override", current_year_market_rate)

        log_debug_event(debug_data, year, step, "ISA Value (Pre-Growth)", my_ISA.asset_value)
        my_ISA.grow_per_year(growth_rate_override=current_year_market_rate)
        log_debug_event(debug_data, year, step, "ISA Value (Post-Growth)", my_ISA.asset_value)
        assert my_ISA.asset_value >= -1e-9, f"Year {year}: ISA value negative ({my_ISA.asset_value})"

        log_debug_event(debug_data, year, step, "GIA Value (Pre-Growth)", my_gia.asset_value)
        my_gia.grow_per_year(growth_rate_override=current_year_market_rate)
        log_debug_event(debug_data, year, step, "GIA Value (Post-Growth)", my_gia.asset_value)
        log_debug_event(debug_data, year, step, "GIA Units", my_gia.units)
        log_debug_event(debug_data, year, step, "GIA Current Unit Price", my_gia.current_unit_price)
        assert my_gia.asset_value >= -1e-9, f"Year {year}: GIA value negative ({my_gia.asset_value})"
        assert my_gia.units >= -1e-9, f"Year {year}: GIA units negative ({my_gia.units})"

        log_debug_event(debug_data, year, step, "Pension Value (Pre-Growth)", my_pension.asset_value)
        my_pension.grow_per_year(growth_rate_override=current_year_market_rate)
        log_debug_event(debug_data, year, step, "Pension Value (Post-Growth)", my_pension.asset_value)
        assert my_pension.asset_value >= -1e-9, f"Year {year}: Pension value negative ({my_pension.asset_value})"

        # --- 3. Pension Contributions & Drawdown Phase ---
        step = "3. Pension Contrib/Drawdown"
        employee_contrib = my_employment.get_employee_pension_contributions(year)
        log_debug_event(debug_data, year, step, "Pension Contribution (Employee)", employee_contrib)
        employer_contrib = my_employment.get_employer_pension_contributions(year)
        log_debug_event(debug_data, year, step, "Pension Contribution (Employer)", employer_contrib)
        total_pension_contributions = employee_contrib + employer_contrib
        log_debug_event(debug_data, year, step, "Pension Contribution (Total)", total_pension_contributions)
        my_pension.put_money(total_pension_contributions)

        # --- PCLS (Lump Sum) Logic ---
        if year == args.retirement_year:
            # Calculate total available PCLS at the moment of retirement
            total_potential_pcls = min(lump_sum_cap, 0.25 * my_pension.asset_value)
            pcls_years_remaining = args.pension_lump_sum_spread_years
            if pcls_years_remaining > 0:
                pcls_annual_amount = total_potential_pcls / pcls_years_remaining
            else:
                pcls_annual_amount = 0 # Should not happen if default is 1
            
            log_debug_event(debug_data, year, step, "PCLS Plan Calculated", total_potential_pcls, f"Spread over {pcls_years_remaining} years: {pcls_annual_amount:.2f}/yr")

        lump_sum_to_take_this_year = 0
        if pcls_years_remaining > 0:
            lump_sum_to_take_this_year = pcls_annual_amount
            pcls_years_remaining -= 1
        
        # --- Regular Drawdown Logic ---
        # Note: draw_down_function now returns ONLY the regular income portion
        regular_drawdown_requested = filipe.pension_draw_down_function(
            pot_value=my_pension.asset_value, current_year=year,
            retirement_year=args.retirement_year, final_year=args.final_year
        )
        
        total_withdrawal_requested = regular_drawdown_requested + lump_sum_to_take_this_year
        
        log_debug_event(debug_data, year, step, "Pension Drawdown Requested", total_withdrawal_requested, f"Regular: {regular_drawdown_requested:.2f}, PCLS: {lump_sum_to_take_this_year:.2f}")
        
        taken_from_pension = my_pension.get_money(total_withdrawal_requested)
        log_debug_event(debug_data, year, step, "Pension Drawdown Actual", taken_from_pension)

        # --- Split into Taxable and Tax-Free ---
        # We prioritize the tax-free lump sum portion. 
        # If we couldn't withdraw enough for the full PCLS, all of it is PCLS.
        # If we withdrew more than PCLS, the rest is taxable.
        actual_lump_sum = min(taken_from_pension, lump_sum_to_take_this_year)
        taxable_pension_income = max(0, taken_from_pension - actual_lump_sum)
        
        if actual_lump_sum > 0:
            filipe.put_in_cash(actual_lump_sum) # Add tax-free cash directly
            log_debug_event(debug_data, year, step, "Cash Add (Pension PCLS)", actual_lump_sum)
            
        log_debug_event(debug_data, year, step, "Taxable Pension Income", taxable_pension_income)


        # --- 4. Tax Calculation Phase ---
        tax_results = calculate_taxes(
            year, args, hmrc, my_employment,
            taxable_salary, gross_interest, taxable_pension_income,
            employee_contrib, employer_contrib, total_pension_contributions,
            dividends=dividends, debug_data=debug_data
        )
        
        # Unpack results
        taxable_interest = tax_results["taxable_interest"]
        pension_allowance = tax_results["pension_allowance"]
        pension_pay_over_allowance = tax_results["pension_pay_over_allowance"]
        total_taxable_income = tax_results["total_taxable_income"]
        income_tax_due = tax_results["income_tax_due"]
        ni_due = tax_results["ni_due"]
        state_pension_income = tax_results["state_pension_income"]
        income_after_tax = tax_results["income_after_tax"]
        
        # Add Net Income to Cash
        filipe.put_in_cash(income_after_tax)
        log_debug_event(debug_data, year, "4. Tax Calculation", "Cash Add (Net Income)", income_after_tax)

        # --- 5. Spending Phase (Living Costs) ---
        step = "5. Living Costs"
        living_costs = filipe.living_costs.get(year, 0)
        log_debug_event(debug_data, year, step, "Living Costs (Required)", living_costs)
        cash_available_pre_costs = filipe.cash
        log_debug_event(debug_data, year, step, "Cash Available (Pre-Costs)", cash_available_pre_costs)

        if living_costs <= cash_available_pre_costs:
            paid_living_costs = filipe.get_from_cash(living_costs)
            extra_cash_needed_to_pay_living_costs = 0
            unpaid_living_costs = 0
            log_debug_event(debug_data, year, step, "Living Costs Payment", paid_living_costs, "Paid fully from cash")
        else:
            paid_living_costs = filipe.get_from_cash(max(0, cash_available_pre_costs - 1)) # Leave £1 buffer
            extra_cash_needed_to_pay_living_costs = living_costs - paid_living_costs
            unpaid_living_costs = extra_cash_needed_to_pay_living_costs
            log_debug_event(debug_data, year, step, "Living Costs Payment", paid_living_costs, f"Partial payment from cash, shortfall={unpaid_living_costs:.2f}")
        log_debug_event(debug_data, year, step, "Cash Available (Post-Costs Payment)", filipe.cash)

        # --- 6. Funding Shortfalls & Buffer Phase ---
        step = "6. Funding Needs"
        buffer_amount = args.buffer_multiplier * living_costs
        log_debug_event(debug_data, year, step, "Buffer Amount Needed", buffer_amount, f"Multiplier={args.buffer_multiplier}")
        extra_cash_needed_all = (extra_cash_needed_to_pay_living_costs + utility_desired + buffer_amount)
        log_debug_event(debug_data, year, step, "Total Cash Needed (Living Shortfall+Utility+Buffer)", extra_cash_needed_all)

        capital_gains = 0; capital_gains_tax = 0; gia_extract_net = 0; amount_taken_from_gia = 0
        if extra_cash_needed_all > 0 and my_gia.asset_value > 0:
            # Simple estimate for GIA gross withdrawal, may result in slightly more CGT or a small second withdrawal.
            estimated_gia_needed_gross = extra_cash_needed_all * (1 + hmrc.capital_gains_tax_rate)
            log_debug_event(debug_data, year, step, "GIA Withdrawal Estimate (Gross)", estimated_gia_needed_gross)
            amount_to_attempt_gia = min(my_gia.asset_value, estimated_gia_needed_gross)
            log_debug_event(debug_data, year, step, "GIA Withdrawal Attempt", amount_to_attempt_gia)

            result = my_gia.get_money(amount_to_attempt_gia)
            if isinstance(result, tuple):
                amount_taken_from_gia, capital_gains = result
                log_debug_event(debug_data, year, step, "GIA Withdrawal Actual", amount_taken_from_gia)
                log_debug_event(debug_data, year, step, "Capital Gains Generated", capital_gains)
                
                # Pass total_taxable_income (calculated in Step 4b) to determine CGT rate
                capital_gains_tax = hmrc.capital_gains_tax_due(capital_gains, total_taxable_income)
                
                log_debug_event(debug_data, year, step, "Capital Gains Tax Due", capital_gains_tax)
                gia_extract_net = amount_taken_from_gia - capital_gains_tax
                log_debug_event(debug_data, year, step, "GIA Withdrawal Net", gia_extract_net)
                filipe.put_in_cash(gia_extract_net)
                log_debug_event(debug_data, year, step, "Cash Add (GIA Net)", gia_extract_net)
            else:
                 # get_money logs warning if failed
                 log_debug_event(debug_data, year, step, "GIA Withdrawal Actual", 0, "Failed/Insufficient")
        else:
             log_debug_event(debug_data, year, step, "GIA Withdrawal Attempt", 0, "Not needed or GIA empty")

        extra_cash_needed_after_gia = max(0, extra_cash_needed_all - gia_extract_net)
        log_debug_event(debug_data, year, step, "Cash Needed (After GIA)", extra_cash_needed_after_gia)

        amount_taken_from_isa = 0
        if extra_cash_needed_after_gia > 0 and my_ISA.asset_value > 0:
            amount_to_attempt_isa = min(my_ISA.asset_value, extra_cash_needed_after_gia)
            log_debug_event(debug_data, year, step, "ISA Withdrawal Attempt", amount_to_attempt_isa)
            amount_taken_from_isa = my_ISA.get_money(amount=amount_to_attempt_isa)
            log_debug_event(debug_data, year, step, "ISA Withdrawal Actual", amount_taken_from_isa)
            filipe.put_in_cash(amount_taken_from_isa)
            log_debug_event(debug_data, year, step, "Cash Add (ISA)", amount_taken_from_isa)
        else:
             log_debug_event(debug_data, year, step, "ISA Withdrawal Attempt", 0, "Not needed or ISA empty")

        extra_cash_needed_after_gia_and_isa = max(0, extra_cash_needed_after_gia - amount_taken_from_isa)
        log_debug_event(debug_data, year, step, "Cash Needed (After ISA)", extra_cash_needed_after_gia_and_isa)
        log_debug_event(debug_data, year, step, "Cash Available (End of Step)", filipe.cash)


        # --- 7. Final Spending & Utility Calculation ---
        step = "7. Utility Spending"
        # Pay remaining living costs if possible
        if unpaid_living_costs > 0:
             can_pay_now = min(unpaid_living_costs, filipe.cash)
             log_debug_event(debug_data, year, step, "Attempting to Pay Unpaid Living Costs", can_pay_now)
             if can_pay_now > 0:
                 paid_now = filipe.get_from_cash(can_pay_now)
                 unpaid_living_costs -= paid_now
                 log_debug_event(debug_data, year, step, "Paid Unpaid Living Costs", paid_now)

        log_debug_event(debug_data, year, step, "Remaining Unpaid Living Costs", unpaid_living_costs)

        # Determine affordable utility
        cash_available_for_utility = max(0, filipe.cash - buffer_amount)
        log_debug_event(debug_data, year, step, "Cash Available for Utility (Post-Buffer)", cash_available_for_utility)
        utility_i_can_afford = min(cash_available_for_utility, utility_desired)
        log_debug_event(debug_data, year, step, "Utility Affordable", utility_i_can_afford)

        # Buy utility / Apply penalty
        if utility_i_can_afford > 0:
             filipe.buy_utility(utility_i_can_afford)
             # Utility value is appended inside buy_utility, retrieve it
             actual_utility_value = filipe.utility[-1] if filipe.utility else 0
             log_debug_event(debug_data, year, step, "Utility Bought", utility_i_can_afford)
             log_debug_event(debug_data, year, step, "Utility Value Added", actual_utility_value)
        else:
             # Apply penalty if living costs remain unpaid
             if unpaid_living_costs > 0:
                 utility_penalty = -(unpaid_living_costs**args.failure_penalty_exponent)
                 filipe.utility.append(utility_penalty)
                 actual_utility_value = utility_penalty
                 utility_i_can_afford = utility_penalty # Reflects negative outcome
                 log_debug_event(debug_data, year, step, "Utility Penalty (Unpaid Living Costs)", utility_penalty, f"Exponent: {args.failure_penalty_exponent}")
             else:
                 filipe.utility.append(0) # Append 0 if no utility bought and no penalty
                 actual_utility_value = 0
                 log_debug_event(debug_data, year, step, "Utility Bought", 0)

        log_debug_event(debug_data, year, step, "Cash Available (Post-Utility)", filipe.cash)

        # --- 7b. Gains Harvesting Phase ---
        step = "7b. Gains Harvesting"
        # Check if we have unused CGT allowance and if the GIA has unrealized gains (price > avg cost)
        remaining_cgt_allowance = hmrc.capital_gains_tax_allowance - capital_gains
        # We only harvest if we have allowance AND the price is higher than the buy price
        if remaining_cgt_allowance > 0 and my_gia.current_unit_price > my_gia.average_unit_buy_price:
            gain_per_unit = my_gia.current_unit_price - my_gia.average_unit_buy_price
            
            # Calculate units to sell to hit the allowance exactly
            # Target Gain = Units * Gain_Per_Unit  =>  Units = Target / Gain_Per_Unit
            units_to_harvest = remaining_cgt_allowance / gain_per_unit
            
            # Don't sell more than we have
            units_to_harvest = min(units_to_harvest, my_gia.units)
            
            if units_to_harvest > 0:
                value_to_harvest = units_to_harvest * my_gia.current_unit_price
                log_debug_event(debug_data, year, step, "Harvesting Attempt", value_to_harvest, f"Target Gain: {remaining_cgt_allowance:.2f}")
                
                # Execute sale
                harvested_amount, harvested_gain = my_gia.get_money(value_to_harvest)
                
                # Update state
                filipe.put_in_cash(harvested_amount)
                capital_gains += harvested_gain # Add to total gains for the year
                
                log_debug_event(debug_data, year, step, "Harvested Amount", harvested_amount)
                log_debug_event(debug_data, year, step, "Harvested Gain", harvested_gain)
        else:
             log_debug_event(debug_data, year, step, "Harvesting Skipped", 0, f"Rem Allowance: {remaining_cgt_allowance:.2f}, Price > Cost: {my_gia.current_unit_price > my_gia.average_unit_buy_price}")


        # --- 8. Investment Phase (Surplus Cash) ---
        step = "8. Investment"
        cash_above_buffer = max(0, filipe.cash - buffer_amount)
        log_debug_event(debug_data, year, step, "Cash Available Above Buffer", cash_above_buffer)

        invested_in_ISA_this_year = 0
        invested_in_GIA_this_year = 0
        isa_allowance_remaining = hmrc.ISA_ANNUAL_ALLOWANCE

        if cash_above_buffer > 0 and isa_allowance_remaining > 0:
            money_for_ISA = min(cash_above_buffer, isa_allowance_remaining)
            log_debug_event(debug_data, year, step, "ISA Investment Attempt", money_for_ISA)
            actual_isa_investment = filipe.get_from_cash(money_for_ISA)
            if actual_isa_investment > 0:
                 my_ISA.put_money(actual_isa_investment)
                 invested_in_ISA_this_year = actual_isa_investment
                 cash_above_buffer -= actual_isa_investment
                 log_debug_event(debug_data, year, step, "ISA Investment Actual", actual_isa_investment)

        if cash_above_buffer > 0:
             log_debug_event(debug_data, year, step, "GIA Investment Attempt", cash_above_buffer)
             actual_gia_investment = filipe.get_from_cash(cash_above_buffer)
             if actual_gia_investment > 0:
                 my_gia.put_money(actual_gia_investment)
                 invested_in_GIA_this_year = actual_gia_investment
                 log_debug_event(debug_data, year, step, "GIA Investment Actual", actual_gia_investment)

        log_debug_event(debug_data, year, step, "Cash Available (End of Year)", filipe.cash)
        assert filipe.cash is not None and not math.isnan(filipe.cash), f"Year {year}: Cash is NaN or None"
        # Allow small negative cash due to potential overdraft penalties/timing
        # assert filipe.cash >= -1e-9, f"Year {year}: Cash negative ({filipe.cash})"


        # --- 9. Logging Phase (End of Year State) ---
        step = "9. Logging"
        total_assets = (my_pension.asset_value + my_ISA.asset_value + my_gia.asset_value +
                        filipe.cash + my_fixed_interest.asset_value + my_NSI.asset_value)
        log_debug_event(debug_data, year, step, "Total Assets (End of Year)", total_assets)
        assert total_assets >= -1e-9, f"Year {year}: Total Assets negative ({total_assets})"

        # Append values to main results lists
        cash_list.append(filipe.cash)
        pension_list.append(my_pension.asset_value)
        ISA_list.append(my_ISA.asset_value)
        GIA_list.append(my_gia.asset_value)
        fixed_interest_list.append(my_fixed_interest.asset_value)
        nsi_list.append(my_NSI.asset_value)
        TOTAL_ASSETS_list.append(total_assets)
        taxable_salary_list.append(taxable_salary)
        gross_interest_list.append(gross_interest + nsi_interest)
        taxable_interest_list.append(taxable_interest)
        capital_gains_list.append(capital_gains)
        capital_gains_tax_list.append(capital_gains_tax)
        pension_allowance_list.append(pension_allowance)
        pension_pay_over_allowance_list.append(pension_pay_over_allowance)
        taken_from_pension_list.append(taken_from_pension)
        taxable_pension_income_list.append(taxable_pension_income)
        total_taxable_income_list.append(total_taxable_income)
        income_tax_due_list.append(income_tax_due)
        national_insurance_due_list.append(ni_due)
        all_tax = ni_due + income_tax_due + capital_gains_tax
        all_tax_list.append(all_tax)
        # Net cash inflow calculation for logging
        # income_after_tax variable above = (Taxable Salary + Taxable Pension - Tax - NI)
        # We need to add back the non-taxable income sources:
        # 1. NSI & Gross Interest (Since tax was deducted from income_after_tax via income_tax_due, but they were not added to income_after_tax base. Wait. 
        # Let's look at income_after_tax def: (taxable_salary + taxable_pension_income - income_tax_due - ni_due)
        # It does NOT include interest. So adding interest here is correct (since interest is cash inflow).
        # 2. Tax-free portion of pension (Lump Sum).
        tax_free_pension_portion = max(0, taken_from_pension - taxable_pension_income)
        
        net_cash_inflow = (income_after_tax 
                          + nsi_interest + gross_interest 
                          + tax_free_pension_portion)
        
        income_after_tax_list.append(net_cash_inflow)
        living_costs_list.append(living_costs)
        utility_i_can_afford_list.append(utility_i_can_afford)
        utility_desired_list.append(utility_desired)
        actual_utility_value_list.append(actual_utility_value)
        invested_in_ISA_list.append(invested_in_ISA_this_year)
        invested_in_GIA_list.append(invested_in_GIA_this_year)
        taken_from_gia_list.append(amount_taken_from_gia)
        taken_from_isa_list.append(amount_taken_from_isa)
        unpaid_living_costs_list.append(unpaid_living_costs)

        logging.info(f"--- Year {year} Complete --- Assets: {total_assets:,.0f}, Cash: {filipe.cash:,.0f}, UtilityVal: {actual_utility_value:.2f}")


    # --- Post-Simulation Analysis ---
    logging.info("Simulation loop finished. Performing post-simulation analysis.")
    final_utility_values = filipe.utility
    if not final_utility_values:
         logging.warning("No utility values recorded during simulation.")
         total_ut, var_ut, std_ut, mean_ut, sigma_ut, discounted_utility = 0, 0, 0, 0, 0, 0
         metric = -8888.888 # Penalize heavily
    else:
        total_ut = round(sum(final_utility_values))
        var_ut = np.var(final_utility_values)
        std_ut = np.std(final_utility_values)
        mean_ut = np.mean(final_utility_values)
        sigma_ut = abs(std_ut / mean_ut) if abs(mean_ut) > 1e-6 else 0
        discounted_utility = npf.npv(args.utility_discount_rate, final_utility_values).round(0)
        metric = discounted_utility - args.volatility_penalty * sigma_ut
        logging.info(f"Post-simulation metrics: Total Utility={total_ut}, Mean={mean_ut:.2f}, Sigma={sigma_ut:.4f}, Discounted={discounted_utility}, Final Metric={metric:.2f}")


    # --- Create Results DataFrame ---
    logging.info("Creating main results DataFrame.")
    df = pd.DataFrame({
        'Cash': cash_list, 'Pension': pension_list, 'ISA': ISA_list, 'GIA': GIA_list,
        'Fixed Interest': fixed_interest_list, 'NSI': nsi_list, 'Total Assets': TOTAL_ASSETS_list,
        'Taxable Salary': taxable_salary_list, 'Gross Interest': gross_interest_list,
        'Taxable Interest': taxable_interest_list, 'Taken from Pension Pot': taken_from_pension_list,
        'Taxable Pension Income': taxable_pension_income_list, 'Income After Tax': income_after_tax_list,
        'Capital Gains': capital_gains_list, 'Capital Gains Tax': capital_gains_tax_list,
        'Pension Allowance': pension_allowance_list, 'Pension Pay Over Allowance': pension_pay_over_allowance_list,
        'Total Taxable Income': total_taxable_income_list, 'Income Tax Due': income_tax_due_list,
        'National Insurance Due': national_insurance_due_list, 'Total Tax': all_tax_list,
        'Living Costs': living_costs_list, 'Utility Desired': utility_desired_list,
        'Utility Affordable': utility_i_can_afford_list, 'Utility Value': actual_utility_value_list,
        'Unpaid Living Costs': unpaid_living_costs_list,
        'Money Invested in ISA': invested_in_ISA_list, 'Money Invested in GIA': invested_in_GIA_list,
        'Amount taken from GIA': taken_from_gia_list, 'Amount taken from ISA': taken_from_isa_list,
    }, index=range(args.start_year, args.final_year + 1))

    logging.info("Simulation function finished.")
    # Return metric, main DataFrame, and the list of debug data dictionaries
    return metric, df, debug_data
