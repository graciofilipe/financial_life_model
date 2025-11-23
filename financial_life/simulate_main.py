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
# Import graph_objects for potentially more control later if needed
import plotly.graph_objects as go
from google.cloud import aiplatform, storage
import numpy_financial as npf

# Import the simulation function
from .simulate_funs import simulate_a_life


# --- Refactored Simulation Logic ---
def run_simulation_and_get_results(params):
    """
    Runs the financial simulation and generates results (metric, DataFrame, plots).

    Args:
        params: An object or dictionary containing simulation parameters
                (similar to the output of argparse.ArgumentParser.parse_args()).

    Returns:
        A tuple containing:
        - metric (float): The final calculated simulation metric.
        - df (pd.DataFrame): The main simulation results DataFrame.
        - plots (dict): A dictionary where keys are plot names (str) and
                        values are Plotly figure objects.
        - debug_data (list or None): The debug data list, or None if not generated.
    """
    logging.info("--- Entering run_simulation_and_get_results ---")

    # GIA_initial_average_buy_price is now handled within the GeneralInvestmentAccount class constructor.
    # The value from params.GIA_initial_average_buy_price (which could be None if not set by user)
    # will be passed directly to the constructor.

    logging.info("Starting financial simulation within run_simulation_and_get_results...")
    # --- Run the simulation ---
    metric = None
    df = None
    debug_data = None
    try:
        # Pass the params object directly to the simulation function
        metric, df, debug_data = simulate_a_life(params)
        logging.info(f"Simulation completed within run_simulation_and_get_results. Final Metric: {metric:.2f}")
    except AssertionError as e:
         logging.critical(f"Assertion failed during simulation: {e}")
         print(f"CRITICAL: Simulation halted due to assertion error: {e}")
         raise # Reraise to signal failure upstream
    except Exception as e:
         logging.critical(f"An unexpected error occurred during simulation: {e}", exc_info=True)
         print(f"CRITICAL: Simulation failed with error: {e}")
         raise # Reraise to signal failure upstream

    # --- Generate Multiple Plots ---
    # Requires 'plotly.express as px' and 'plotly.graph_objects as go' imports
    logging.info("Generating plots within run_simulation_and_get_results...")
    plots = {} # Dictionary to hold plot figures

    # Define column groups for plots
    plot_groups = {
        "Assets": ['Total Assets', 'Pension', 'ISA', 'GIA', 'Cash', 'Fixed Interest', 'NSI'],
        "Income_Tax_Summary": ['Taxable Salary', 'Total Taxable Income', 'Total Tax', 'Income After Tax'],
        "Utility": ['Utility Desired', 'Utility Affordable', 'Utility Value'],
        "Living_Costs": ['Living Costs', 'Unpaid Living Costs'],
        "Investment_Flows": ['Money Invested in ISA', 'Money Invested in GIA', 'Amount taken from GIA', 'Amount taken from ISA'],
        "Tax_Details": ['Taxable Interest', 'Capital Gains Tax', 'Income Tax Due', 'National Insurance Due', 'Pension Pay Over Allowance']
    }

    # Create a plot for each group
    if df is not None: # Only try plotting if simulation produced a DataFrame
        for group_name, columns in plot_groups.items():
            try:
                # Filter columns that actually exist in the DataFrame
                valid_cols = [col for col in columns if col in df.columns]
                if valid_cols:
                    # Use plotly express for simplicity
                    fig = px.line(df, x=df.index, y=valid_cols,
                                  title=f'{group_name.replace("_", " ")} Over Time ({params.file_name})') # Use params.file_name
                    fig.update_xaxes(title_text='Year')
                    fig.update_yaxes(title_text='Value (£)')
                    fig.update_layout(hovermode="x unified")
                    plots[group_name] = fig # Store the figure
                    logging.info(f"Generated plot: {group_name}")
                else:
                    logging.warning(f"Skipping plot '{group_name}': No valid columns found in DataFrame.")
            except Exception as e:
                logging.error(f"Error creating plot for group '{group_name}': {e}", exc_info=True)
    else:
        logging.warning("Skipping plot generation as simulation DataFrame is None.")


    logging.info("--- Exiting run_simulation_and_get_results ---")
    # Return the calculated metric, dataframe, generated plots, and debug data
    return metric, df, plots, debug_data


# --- Main Execution Logic ---
def main():
    print("--- simulate_main.py execution started ---", flush=True) # Added for immediate execution feedback
    """
    Parses command-line arguments, sets up logging, runs the simulation,
    and saves results (main DataFrame, debug DataFrame, multiple plot files).
    """
    parser = argparse.ArgumentParser(description="Run a financial life simulation.")

    # --- General & Simulation Arguments ---
    parser.add_argument("--bucket_name", required=True, help="GCS bucket name to save results.")
    parser.add_argument("--file_name", default="sim_results", help="Base name for output files.")
    parser.add_argument("--start_year", type=int, default=2025, help="Simulation start year.")
    parser.add_argument("--final_year", type=int, default=2074, help="Simulation end year.")
    parser.add_argument("--retirement_year", type=int, default=2055, help="Year of retirement.")

    parser.add_argument("--pension_lump_sum_spread_years", type=int, default=1, help="Number of years to spread the pension tax-free lump sum over (Phased Drawdown).")

    # --- Initial Capital Arguments ---
    parser.add_argument("--starting_cash", type=float, default=5000, help="Initial cash on hand.")
    parser.add_argument("--fixed_interest_capital", type=float, default=1000, help="Initial capital in fixed interest account.")
    parser.add_argument("--NSI_capital", type=float, default=50000, help="Initial capital in NSI account.")
    parser.add_argument("--pension_capital", type=float, default=150000, help="Initial pension capital.")
    parser.add_argument("--ISA_capital", type=float, default=150000, help="Initial ISA capital.")

    # --- GIA Initial State Arguments ---
    parser.add_argument("--GIA_capital", type=float, default=500000, help="Initial total value of GIA capital.")
    parser.add_argument("--GIA_initial_units", type=float, default=100.0, help="Initial number of units held in GIA.")
    parser.add_argument("--GIA_initial_average_buy_price", type=float, default=None, help="Optional: Initial average buy price per unit for GIA. If None, calculated from GIA_capital / GIA_initial_units.")

    # --- Rate/Growth Arguments ---
    parser.add_argument("--fixed_interest_rate", type=float, default=0.02, help="Annual interest rate for fixed interest account.")
    parser.add_argument("--NSI_interest_rate", type=float, default=0.02, help="Annual interest rate for NSI account.")
    parser.add_argument("--pension_growth_rate", type=float, default=0.02, help="Annual growth rate for pension investments.")
    parser.add_argument("--ISA_growth_rate", type=float, default=0.02, help="Annual growth rate for ISA investments.")
    parser.add_argument("--GIA_growth_rate", type=float, default=0.02, help="Annual growth rate for GIA investments.")
    parser.add_argument("--living_costs_rate_pre_retirement", type=float, default=0.02, help="Annual living costs growth rate before retirement (e.g., 0.02 for 2%).")
    parser.add_argument("--living_costs_rate_post_retirement", type=float, default=0.04, help="Annual living costs growth rate after retirement (e.g., 0.04 for 4%).")
    parser.add_argument("--salary_growth_rate", type=float, default=0.01, help="Annual gross salary growth rate (e.g., 0.01 for 1%).")
    parser.add_argument("--salary_growth_stop_year", type=int, default=None, help="Year after which salary growth stops (plateaus). If not set, grows until retirement.")
    parser.add_argument("--salary_post_plateau_growth_rate", type=float, default=0.0, help="Annual salary growth rate AFTER the stop year (e.g., -0.01 for 1% decline). Default 0.0.")
    # --- Base Value Arguments ---
    parser.add_argument("--base_living_cost", type=float, default=20000, help="Base living cost amount in the start year.")
    parser.add_argument("--base_salary", type=float, default=100000, help="Base gross salary amount in the year before the start year.")

    # --- Employment Arguments ---
    parser.add_argument("--employee_pension_contributions_pct", type=float, default=0.07, help="Employee pension contribution as a percentage of gross salary (e.g., 0.07 for 7%).")
    parser.add_argument("--employer_pension_contributions_pct", type=float, default=0.07, help="Employer pension contribution as a percentage of gross salary (e.g., 0.07 for 7%).")

    # --- Strategy Arguments ---
    parser.add_argument("--buffer_multiplier", type=float, default=1.2, help="Multiplier for cash buffer based on current year's living costs.")

    # --- Utility Function Arguments ---
    parser.add_argument("--utility_baseline", type=float, default=30000, help="Baseline desired utility spending in the start year.")
    parser.add_argument("--utility_linear_rate", type=float, default=0, help="Absolute amount (£) to add to baseline utility each year.")
    parser.add_argument("--utility_exp_rate", type=float, default=0.005, help="Exponential growth rate for utility per year (e.g., 0.01 for 1%).")
    parser.add_argument("--non_linear_utility", type=float, default=0.99, help="Exponent for calculating actual utility from spending (e.g., 0.5 for sqrt).")
    parser.add_argument("--utility_discount_rate", type=float, default=0.001, help="Discount rate for calculating net present value of utility.")
    parser.add_argument("--volatility_penalty", type=float, default=100000, help="Penalty factor for utility volatility (stdev/mean) in the final metric.")

    # --- Troubleshooting Arguments ---
    parser.add_argument("--log_level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the logging level for console output.")
    parser.add_argument("--save_debug_data", action='store_true', help="Save the detailed debug DataFrame to GCS.")

    # --- One-Off Expenses ---
    parser.add_argument("--one_off_expenses", type=str, default="{}", help="JSON string mapping years to one-off expense amounts (e.g., '{\"2030\": 50000}').")

    args = parser.parse_args()

    # --- Parse One-Off Expenses ---
    try:
        args.one_off_expenses = json.loads(args.one_off_expenses)
    except json.JSONDecodeError as e:
        print(f"Error parsing --one_off_expenses: {e}")
        sys.exit(1)

    # --- Setup Logging ---
    log_level_numeric = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level_numeric,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("Logging configured with level: %s", args.log_level.upper())

    # --- Run Simulation & Get Results ---
    logging.info("Calling run_simulation_and_get_results...")
    metric, df, plots, debug_data = None, None, None, None # Initialize results
    try:
        # Pass the parsed args object directly
        metric, df, plots, debug_data = run_simulation_and_get_results(args)
        # Basic check if results seem valid (can be expanded)
        if metric is None or df is None or plots is None:
             logging.critical("Simulation function did not return expected values. Exiting.")
             print("CRITICAL: Simulation failed internally. Check logs.")
             return # Stop execution
        logging.info(f"Simulation successful. Metric: {metric:.2f}. DataFrame shape: {df.shape}. Plots generated: {len(plots)}")
    except Exception as e:
        # Catch exceptions raised from run_simulation_and_get_results
        logging.critical(f"Simulation failed during execution: {e}", exc_info=True)
        print(f"CRITICAL: Simulation execution failed. Check logs for details.")
        return # Stop execution


    # --- Save results to GCS ---
    # Only proceed if simulation was successful (df is not None)
    if df is not None:
        logging.info("Saving results to GCS bucket: %s", args.bucket_name)
        try:
            from google.cloud import storage
            import os
            from datetime import datetime

            storage_client = storage.Client()
            bucket = storage_client.bucket(args.bucket_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save each generated plot (using the 'plots' dict returned from the function)
            if plots: # Check if plots dictionary is not empty
                for group_name, fig in plots.items():
                    try:
                        file_name_html = f'{args.file_name}_plot_{group_name}_{timestamp}.html'
                        temp_file_path_html = f"/tmp/{file_name_html}"
                        fig.write_html(temp_file_path_html)
                        blob_html = bucket.blob(file_name_html)
                        blob_html.upload_from_filename(temp_file_path_html)
                        os.remove(temp_file_path_html)
                        logging.info(f"Plot '{group_name}' uploaded to gs://{args.bucket_name}/{file_name_html}")
                    except Exception as e:
                        logging.error(f"Error saving plot '{group_name}' to GCS: {e}", exc_info=True)
            else:
                 logging.warning("No plots were generated or returned to save.")


            # Save main DataFrame (using the 'df' returned from the function)
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

            # Save debug DataFrame if requested and available (using 'debug_data' returned)
            if args.save_debug_data and debug_data:
                try:
                    debug_df = pd.DataFrame(debug_data)
                    file_name_debug_csv = f'{args.file_name}_debug_data_{timestamp}.csv'
                    temp_file_path_debug_csv = f"/tmp/{file_name_debug_csv}"
                    debug_df.to_csv(temp_file_path_debug_csv, index=False)
                    blob_debug_csv = bucket.blob(file_name_debug_csv)
                    blob_debug_csv.upload_from_filename(temp_file_path_debug_csv)
                    os.remove(temp_file_path_debug_csv)
                    logging.info(f"Debug data uploaded to gs://{args.bucket_name}/{file_name_debug_csv}")
                except Exception as e:
                    logging.error(f"Error saving debug data to GCS: {e}", exc_info=True)
            elif args.save_debug_data:
                 logging.warning("Flag --save_debug_data was set, but no debug data was generated/returned by the simulation function.")

        except Exception as e:
            logging.critical(f"Error interacting with GCS: {e}", exc_info=True)
            print(f"CRITICAL: Failed to save results to GCS. Ensure bucket name is correct and permissions are set.")
    else:
        logging.error("Skipping GCS save because simulation failed and DataFrame is None.")

    logging.info("Script finished.")

if __name__ == "__main__":
    main()
