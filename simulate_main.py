import argparse
import datetime
import json
import os
from datetime import datetime
import math # For isnan check
import logging # Import logging module

# Third-party imports
import pandas as pd
import plotly.express as px
from google.cloud import aiplatform, storage
import numpy_financial as npf

# Import the simulation function
from simulate_funs import simulate_a_life


def main():
    """
    Parses command-line arguments, sets up logging, runs the simulation,
    and saves results (main DataFrame, debug DataFrame, plot).
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
    parser.add_argument("--utility_baseline", type=float, default=30000, help="Baseline desired utility spending in the start year.")
    parser.add_argument("--utility_linear_rate", type=float, default=0, help="Absolute amount (£) to add to baseline utility each year.")
    parser.add_argument("--utility_exp_rate", type=float, default=0.0, help="Exponential growth rate for utility per year (e.g., 0.01 for 1%).")
    parser.add_argument("--non_linear_utility", type=float, default=1, help="Exponent for calculating actual utility from spending (e.g., 0.5 for sqrt).")
    parser.add_argument("--utility_discount_rate", type=float, default=0.02, help="Discount rate for calculating net present value of utility.")
    parser.add_argument("--volatility_penalty", type=float, default=100000, help="Penalty factor for utility volatility (stdev/mean) in the final metric.")

    # --- Troubleshooting Arguments ---
    parser.add_argument("--log_level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the logging level for console output.")
    parser.add_argument("--save_debug_data", action='store_true', help="Save the detailed debug DataFrame to GCS.") # Changed to flag

    args = parser.parse_args()

    # --- Setup Logging ---
    log_level_numeric = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level_numeric,
                        format='%(asctime)s - %(levelname)s - %(message)s', # Added timestamp
                        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("Logging configured with level: %s", args.log_level.upper())


    # --- Calculate default GIA initial average buy price if needed ---
    if args.GIA_initial_average_buy_price is None:
        if args.GIA_initial_units > 0 and args.GIA_capital >= 0:
            args.GIA_initial_average_buy_price = args.GIA_capital / args.GIA_initial_units
            logging.info(f"Calculated default GIA initial average buy price: {args.GIA_initial_average_buy_price:.4f}")
        elif args.GIA_initial_units == 0 and args.GIA_capital == 0:
             args.GIA_initial_average_buy_price = 0.0 # Empty account
             logging.info("GIA starts empty, initial average buy price set to 0.")
        else:
             logging.warning(f"Inconsistent GIA initial state (Capital={args.GIA_capital}, Units={args.GIA_initial_units}) and no average buy price provided. Setting price to 0.")
             args.GIA_initial_average_buy_price = 0.0

    if math.isnan(args.GIA_initial_average_buy_price):
        logging.warning("Calculated GIA initial average buy price is NaN. Setting to 0.")
        args.GIA_initial_average_buy_price = 0.0

    logging.info("Starting financial simulation...")
    # --- Run the simulation ---
    # Now returns metric, main df, and debug data list
    try:
        metric, df, debug_data = simulate_a_life(args)
        logging.info(f"Simulation completed. Final Metric: {metric:.2f}")
    except AssertionError as e:
         logging.critical(f"Assertion failed during simulation: {e}")
         print(f"CRITICAL: Simulation halted due to assertion error: {e}")
         # Optionally save partial results or debug info here before exiting
         return # Stop execution
    except Exception as e:
         logging.critical(f"An unexpected error occurred during simulation: {e}", exc_info=True)
         print(f"CRITICAL: Simulation failed with error: {e}")
         return # Stop execution


    # --- Plot results ---
    plot_columns = ['Cash', 'Pension', 'ISA', 'GIA', 'Total Assets', 'Utility Value', 'Living Costs', 'Total Tax']
    fig = None # Initialize fig to None
    try:
        # Check if required columns exist in the DataFrame
        valid_plot_columns = [col for col in plot_columns if col in df.columns]
        if valid_plot_columns:
            fig = px.line(df, x=df.index, y=valid_plot_columns,
                            title=f'Financial Simulation Results ({args.file_name})')
            fig.update_xaxes(title_text='Year')
            fig.update_yaxes(title_text='Value (£)')
            fig.update_layout(hovermode="x unified")
            logging.info("Plot generated successfully.")
        else:
            logging.warning("No valid columns found for plotting.")
    except Exception as e:
        logging.error(f"Error creating plot: {e}", exc_info=True)


    # --- Save results to GCS ---
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(args.bucket_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save plot if created successfully
        if fig:
            try:
                file_name_html = f'{args.file_name}_plot_{timestamp}.html'
                temp_file_path_html = f"/tmp/{file_name_html}"
                fig.write_html(temp_file_path_html)
                blob_html = bucket.blob(file_name_html)
                blob_html.upload_from_filename(temp_file_path_html)
                os.remove(temp_file_path_html)
                logging.info(f"Plot uploaded to gs://{args.bucket_name}/{file_name_html}")
            except Exception as e:
                logging.error(f"Error saving plot to GCS: {e}", exc_info=True)

        # Save main DataFrame
        try:
            file_name_csv = f'{args.file_name}_data_{timestamp}.csv'
            temp_file_path_csv = f"/tmp/{file_name_csv}"
            df.to_csv(temp_file_path_csv)
            blob_csv = bucket.blob(file_name_csv)
            blob_csv.upload_from_filename(temp_file_path_csv)
            os.remove(temp_file_path_csv)
            logging.info(f"Main data uploaded to gs://{args.bucket_name}/{file_name_csv}")
        except Exception as e:
            logging.error(f"Error saving main data to GCS: {e}", exc_info=True)

        # Save debug DataFrame if requested
        if args.save_debug_data and debug_data:
            try:
                debug_df = pd.DataFrame(debug_data)
                file_name_debug_csv = f'{args.file_name}_debug_data_{timestamp}.csv'
                temp_file_path_debug_csv = f"/tmp/{file_name_debug_csv}"
                debug_df.to_csv(temp_file_path_debug_csv, index=False) # No need for index col
                blob_debug_csv = bucket.blob(file_name_debug_csv)
                blob_debug_csv.upload_from_filename(temp_file_path_debug_csv)
                os.remove(temp_file_path_debug_csv)
                logging.info(f"Debug data uploaded to gs://{args.bucket_name}/{file_name_debug_csv}")
            except Exception as e:
                logging.error(f"Error saving debug data to GCS: {e}", exc_info=True)
        elif args.save_debug_data:
             logging.warning("Flag --save_debug_data was set, but no debug data was generated/returned.")

    except Exception as e:
        logging.critical(f"Error interacting with GCS: {e}", exc_info=True)
        print(f"CRITICAL: Failed to save results to GCS. Ensure bucket name is correct and permissions are set.")


if __name__ == "__main__":
    main()
