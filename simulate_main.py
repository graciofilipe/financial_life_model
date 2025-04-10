import argparse
from simulate_funs import simulate_a_life
import argparse
import datetime
import json
import os
from datetime import datetime
import math # For isnan check

# Third-party imports
import plotly.express as px
from google.cloud import aiplatform, storage
import numpy_financial as npf # Ensure numpy_financial is imported if used directly here (it's used in simulate_funs)


def main():
    """
    Parses command-line arguments and runs the simulate_a_life function.
    """
    parser = argparse.ArgumentParser(description="Run a financial life simulation.")

    # --- General & Simulation Arguments ---
    parser.add_argument("--bucket_name", required=True, help="GCS bucket name to save results.")
    parser.add_argument("--file_name", default="sim_results", help="Base name for output files.")
    parser.add_argument("--start_year", type=int, default=2025, help="Simulation start year.")
    parser.add_argument("--final_year", type=int, default=2074, help="Simulation end year.")
    parser.add_argument("--retirement_year", type=int, default=2055, help="Year of retirement.")

    # --- Initial Capital Arguments ---
    parser.add_argument("--starting_cash", type=float, default=5000, help="Initial cash on hand.")
    parser.add_argument("--fixed_interest_capital", type=float, default=1000, help="Initial capital in fixed interest account.")
    parser.add_argument("--NSI_capital", type=float, default=10000, help="Initial capital in NSI account.")
    parser.add_argument("--pension_capital", type=float, default=50000, help="Initial pension capital.")
    parser.add_argument("--ISA_capital", type=float, default=50000, help="Initial ISA capital.")

    # --- GIA Initial State Arguments ---
    parser.add_argument("--GIA_capital", type=float, default=50000, help="Initial total value of GIA capital.")
    parser.add_argument("--GIA_initial_units", type=float, default=100.0, help="Initial number of units held in GIA.")
    parser.add_argument("--GIA_initial_average_buy_price", type=float, default=None, help="Optional: Initial average buy price per unit for GIA. If None, calculated from GIA_capital / GIA_initial_units.")

    # --- Rate/Growth Arguments ---
    parser.add_argument("--fixed_interest_rate", type=float, default=0.02, help="Annual interest rate for fixed interest account.")
    parser.add_argument("--NSI_interest_rate", type=float, default=0.02, help="Annual interest rate for NSI account.")
    parser.add_argument("--pension_growth_rate", type=float, default=0.02, help="Annual growth rate for pension investments.")
    parser.add_argument("--ISA_growth_rate", type=float, default=0.02, help="Annual growth rate for ISA investments.")
    parser.add_argument("--GIA_growth_rate", type=float, default=0.02, help="Annual growth rate for GIA investments.")

    # --- Employment Arguments ---
    parser.add_argument("--employee_pension_contributions_pct", type=float, default=0.07, help="Employee pension contribution as a percentage of gross salary (e.g., 0.07 for 7%).")
    parser.add_argument("--employer_pension_contributions_pct", type=float, default=0.07, help="Employer pension contribution as a percentage of gross salary (e.g., 0.07 for 7%).")

    # --- Strategy Arguments ---
    parser.add_argument("--CG_strategy", default="harvest", help="Capital gains strategy (currently 'harvest' - not actively used in logic).")
    parser.add_argument("--buffer_multiplier", type=float, default=1.2, help="Multiplier for cash buffer based on current year's living costs.")

    # --- Utility Function Arguments ---
    # Removed old block arguments
    parser.add_argument("--utility_baseline", type=float, default=30000, help="Baseline desired utility spending in the start year.")
    parser.add_argument("--utility_linear_rate", type=float, default=0, help="Absolute amount (£) to add to baseline utility each year.")
    parser.add_argument("--utility_exp_rate", type=float, default=0.0, help="Exponential growth rate for utility per year (e.g., 0.01 for 1%).")

    parser.add_argument("--non_linear_utility", type=float, default=1, help="Exponent for calculating actual utility from spending (e.g., 0.5 for sqrt).")
    parser.add_argument("--utility_discount_rate", type=float, default=0.02, help="Discount rate for calculating net present value of utility.")
    parser.add_argument("--volatility_penalty", type=float, default=100000, help="Penalty factor for utility volatility (stdev/mean) in the final metric.")


    args = parser.parse_args()

    # --- Calculate default GIA initial average buy price if needed ---
    if args.GIA_initial_average_buy_price is None:
        if args.GIA_initial_units > 0 and args.GIA_capital >= 0:
            args.GIA_initial_average_buy_price = args.GIA_capital / args.GIA_initial_units
            print(f"Calculated default GIA initial average buy price: {args.GIA_initial_average_buy_price:.4f}")
        elif args.GIA_initial_units == 0 and args.GIA_capital == 0:
             args.GIA_initial_average_buy_price = 0.0 # Empty account
             print("GIA starts empty, initial average buy price set to 0.")
        else:
             print(f"Warning: Inconsistent GIA initial state (Capital={args.GIA_capital}, Units={args.GIA_initial_units}) and no average buy price provided. Setting price to 0.")
             args.GIA_initial_average_buy_price = 0.0

    if math.isnan(args.GIA_initial_average_buy_price):
        print("Warning: Calculated GIA initial average buy price is NaN. Setting to 0.")
        args.GIA_initial_average_buy_price = 0.0


    # --- Run the simulation ---
    metric, df = simulate_a_life(args)
    print(f"Simulation completed. Final Metric: {metric:.2f}")

    # --- Plot results ---
    plot_columns = ['Cash', 'Pension', 'ISA', 'GIA', 'Total Assets', 'Utility Value', 'Living Costs', 'Total Tax']
    try:
        fig = px.line(df, x=df.index, y=[col for col in plot_columns if col in df.columns],
                        title=f'Financial Simulation Results ({args.file_name})')
        fig.update_xaxes(title_text='Year')
        fig.update_yaxes(title_text='Value (£)')
        fig.update_layout(hovermode="x unified")
    except Exception as e:
        print(f"Error creating plot: {e}")
        fig = None

    # --- Save results to GCS ---
    # (Saving logic remains the same)
    storage_client = storage.Client()
    bucket = storage_client.bucket(args.bucket_name)
    if fig:
        try:
            file_name_html = f'{args.file_name}_plot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
            temp_file_path_html = f"/tmp/{file_name_html}"
            fig.write_html(temp_file_path_html)
            blob_html = bucket.blob(file_name_html)
            blob_html.upload_from_filename(temp_file_path_html)
            os.remove(temp_file_path_html)
            print(f"Plot uploaded to gs://{args.bucket_name}/{file_name_html}")
        except Exception as e:
            print(f"Error saving plot to GCS: {e}")
    try:
        file_name_csv = f'{args.file_name}_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        temp_file_path_csv = f"/tmp/{file_name_csv}"
        df.to_csv(temp_file_path_csv)
        blob_csv = bucket.blob(file_name_csv)
        blob_csv.upload_from_filename(temp_file_path_csv)
        os.remove(temp_file_path_csv)
        print(f"Data uploaded to gs://{args.bucket_name}/{file_name_csv}")
    except Exception as e:
        print(f"Error saving data to GCS: {e}")
        print("Please ensure the bucket name is correct and you have write permissions.")


if __name__ == "__main__":
    main()
