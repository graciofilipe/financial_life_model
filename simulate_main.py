import argparse
from simulate_funs import simulate_a_life
import argparse
import datetime
import json
import os
from datetime import datetime

# Third-party imports
import plotly.express as px
from google.cloud import aiplatform, storage


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
    parser.add_argument("--GIA_capital", type=float, default=50000, help="Initial GIA capital.")

    # --- Rate/Growth Arguments ---
    parser.add_argument("--fixed_interest_rate", type=float, default=0.02, help="Annual interest rate for fixed interest account.")
    parser.add_argument("--NSI_interest_rate", type=float, default=0.02, help="Annual interest rate for NSI account.")
    parser.add_argument("--pension_growth_rate", type=float, default=0.02, help="Annual growth rate for pension investments.")
    parser.add_argument("--ISA_growth_rate", type=float, default=0.02, help="Annual growth rate for ISA investments.")
    parser.add_argument("--GIA_growth_rate", type=float, default=0.02, help="Annual growth rate for GIA investments.")

    # --- Strategy Arguments ---
    parser.add_argument("--CG_strategy", default="harvest", help="Capital gains strategy (currently 'harvest').") # Consider making this more flexible if needed
    parser.add_argument("--buffer_multiplier", type=float, default=1.2, help="Multiplier for cash buffer based on living costs.")

    # --- Utility Function Arguments ---
    parser.add_argument("--non_linear_utility", type=float, default=1, help="Exponent for non-linear utility calculation.")
    parser.add_argument("--utility_discount_rate", type=float, default=0.02, help="Discount rate for calculating net present value of utility. Used only for optimisation")

    # --- Utility Parameters (Default values) ---
    parser.add_argument("--utility_2024_2029", type=float, default=30000)
    parser.add_argument("--utility_2030_2034", type=float, default=30000)
    parser.add_argument("--utility_2035_2039", type=float, default=30000)
    parser.add_argument("--utility_2040_2044", type=float, default=30000)
    parser.add_argument("--utility_2045_2049", type=float, default=30000)
    parser.add_argument("--utility_2050_2054", type=float, default=30000)
    parser.add_argument("--utility_2055_2059", type=float, default=30000)
    parser.add_argument("--utility_2060_2064", type=float, default=30000)
    parser.add_argument("--utility_2065_2069", type=float, default=30000)
    parser.add_argument("--utility_2070_2074", type=float, default=30000)

    args = parser.parse_args()

    # Run the simulation
    metric, df = simulate_a_life(args)
    print(f"Simulation completed. Metric: {metric}")
    print(f"Dataframe: {df}")

    # Plot results
    fig = px.line(df, x=df.index, y=df.columns,
                    title=f'Financial Simulation')
    fig.update_xaxes(title_text='Year')
    fig.update_yaxes(title_text='Value')

    # Save plot to GCS
    file_name = f'{args.file_name}_optimal_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    temp_file_path = f"/tmp/{file_name}"
    fig.write_html(temp_file_path)

    storage_client = storage.Client()
    bucket = storage_client.bucket(args.bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_filename(temp_file_path)
    os.remove(temp_file_path) # Clean up temp file
    print(f"plot uploaded to gs://{args.bucket_name}/{file_name}")


if __name__ == "__main__":
    main()
