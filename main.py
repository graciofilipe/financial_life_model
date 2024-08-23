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
from simulate import simulate_a_life


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


if __name__ == "__main__":

    # get the project id from environment variable: 
    project_id = os.environ.get('PROJECT_ID')
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket_name", required=True)
    parser.add_argument("--start_year", required=False, default=2024)
    parser.add_argument("--final_year", required=False, default=2074)
    parser.add_argument("--retirement_year", required=False, default=2054)
    
    parser.add_argument("--starting_cash", required=False, default=10000)
    
    parser.add_argument("--fixed_interest_capital", required=False, default=1000)
    parser.add_argument("--fixed_interest_rate", required=False, default=0.02)

    parser.add_argument("--NSI_capital", required=False, default=50000)
    parser.add_argument("--NSI_interest_rate", required=False, default=0.02)

    parser.add_argument("--pension_capital", required=False, default=100000)
    parser.add_argument("--pension_growth_rate", required=False, default=0.03)

    parser.add_argument("--ISA_capital", required=False, default=100000)
    parser.add_argument("--ISA_growth_rate", required=False, default=0.03)

    parser.add_argument("--GIA_capital", required=False, default=100000)
    parser.add_argument("--GIA_growth_rate", required=False, default=0.03)

    parser.add_argument("--CG_strategy", required=False, default="harvest")

    parser.add_argument("--buffer_multiplier", required=False, default=1.1)

    parser.add_argument("--utility_income_multiplier", required=False, default=0.5)
    parser.add_argument("--utility_investments_multiplier", required=False, default=0.1)
    parser.add_argument("--utility_pension_multiplier", required=False, default=0.03)
    parser.add_argument("--utility_cap", required=False, default=50000)

    args = parser.parse_args()

    simulate_a_life(args)

    # df = pd.DataFrame({
    #     'Taxable Salary': taxable_salary_list,
    #     'Gross Interest': gross_interest_list,
    #     'Taxable Interest': taxable_interest_list,
    #     'Capital Gains': capital_gains_list,
    #     'Capital Gains Tax': capital_gains_tax_list,
    #     'Pension Allowance': pension_allowance_list,
    #     'Pension Pay Over Allowance': pension_pay_over_allowance_list,
    #     'Taken from Pension Pot': taken_from_pension_list,
    #     'Total Taxable Income': total_taxable_income_list,
    #     'Income Tax Due': income_tax_due_list,
    #     'National Insurance Due': national_insurance_due_list,
    #     'Total Tax': all_tax_list,
    #     'Amount Needed from GIA': ammount_needed_from_gia_list,
    #     'Living Costs': living_costs_list,
    #     'Income After Tax': income_after_tax_list,
    #     'Cash': cash_list,
    #     'Pension': pension_list,
    #     'ISA': ISA_list,
    #     'GIA': GIA_list,
    #     'Utility': filipe.utility,
    #     'Total Assets': TOTAL_ASSETS_list,
    #     'Money Invested in ISA': money_invested_in_ISA,
    #     'Money Invested in GIA': money_invested_in_GIA,
    # }, index=range(args.start_year, args.final_year))


    # fig = px.line(df, x=df.index, y=df.columns, title='Financial Simulation')
    # fig.update_xaxes(title_text='Year')
    # fig.update_yaxes(title_text='Value')
    
    # # Write to GCS
    # file_name = f'sim_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    # storage_client = storage.Client()
    # bucket = storage_client.bucket(bucket_name)
    # blob = bucket.blob(file_name)
    # fig.write_html(f"/tmp/{file_name}")
    # blob.upload_from_filename(f"/tmp/{file_name}")
    # print(f"HTML file uploaded to gs://{bucket_name}/{file_name}")

    

