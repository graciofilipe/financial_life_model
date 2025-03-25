import argparse
import datetime
import json
import os
from datetime import datetime

# Third-party imports
import plotly.express as px
from google.cloud import aiplatform, storage

# Local application imports
from simulate import simulate_a_life


def run_vizier_study(args):
    """
    Sets up and runs a Vizier study for financial simulation optimization.

    Args:
        args: Command-line arguments containing simulation parameters and
              Vizier configuration.

    Returns:
        None. Outputs results and optionally plots to GCS.
    """
    REGION = "europe-west1"
    PROJECT_ID = os.environ.get('PROJECT_ID')
    if not PROJECT_ID:
        raise ValueError("Environment variable PROJECT_ID is not set.")

    STUDY_DISPLAY_NAME = '{}_study_{}'.format(
        PROJECT_ID.replace('-', ''), datetime.now().strftime('%Y%m%d_%H%M%S')
    )
    ENDPOINT = f'{REGION}-aiplatform.googleapis.com'
    PARENT = f'projects/{PROJECT_ID}/locations/{REGION}'

    # --- Define Vizier Study Parameters ---
    # Parameters define the search space for optimization.
    # Each parameter has an ID, type (double, integer, categorical, discrete),
    # and specifies the range or values.

    # Example commented-out parameters (can be removed or adapted):
    # param_utility_income_multiplier_work = {
    #     'parameter_id': 'utility_income_multiplier_work',
    #     'double_value_spec': {'min_value': 0.01, 'max_value': 1.2}
    # }
    # ... other commented params ...

    # Define parameters for utility values over different periods
    param_utility_specs = []
    utility_periods = [
        (2024, 2029, 5000, 100000),
        (2030, 2034, 5000, 100000),
        (2035, 2039, 5000, 500000),
        (2040, 2044, 5000, 500000),
        (2045, 2049, 5000, 500000),
        (2050, 2054, 5000, 1000000),
        (2055, 2059, 5000, 1000000),
        (2060, 2064, 5000, 1000000),
        (2065, 2069, 5000, 1000000),
        (2070, 2074, 5000, 1000000),
    ]

    for start, end, min_val, max_val in utility_periods:
        param_utility_specs.append({
            'parameter_id': f'utility_{start}_{end}',
            'double_value_spec': {
                'min_value': float(min_val),
                'max_value': float(max_val)
            }
        })

    # --- Define Vizier Study Metric ---
    # The metric to optimize (e.g., maximize discounted utility).
    metric_utility = {
        'metric_id': 'discounted_utility',
        'goal': 'MAXIMIZE'
    }

    # --- Create Vizier Study Spec ---
    study_spec = {
        'algorithm': 'ALGORITHM_UNSPECIFIED', # Default algorithm
        'parameters': param_utility_specs,
        'metrics': [metric_utility],
    }

    study = {
        'display_name': STUDY_DISPLAY_NAME,
        'study_spec': study_spec
    }

    # --- Initialize Vizier Client and Create Study ---
    vizier_client = aiplatform.gapic.VizierServiceClient(
        client_options=dict(api_endpoint=ENDPOINT)
    )
    study = vizier_client.create_study(parent=PARENT, study=study)
    STUDY_NAME = study.name
    print(f"Created Vizier study: {STUDY_NAME}")

    # --- Run Vizier Trials ---
    num_trials = int(args.num_trials)
    if num_trials > 1:
        print(f"Running {num_trials} Vizier trials...")
        for i in range(num_trials):
            print(f"--- Trial {i + 1}/{num_trials} ---")
            try:
                suggest_response = vizier_client.suggest_trials({
                    'parent': STUDY_NAME,
                    'suggestion_count': 1,
                    # 'client_id': f'trial_{i}' # Optional client ID
                })

                trial = suggest_response.result().trials[0]
                trial_parameters = {p.parameter_id: p.value for p in trial.parameters}
                print(f"Suggested parameters: {trial_parameters}")

                # Update args with suggested parameters
                for param_id, value in trial_parameters.items():
                    setattr(args, param_id, value)

                # Run the simulation with the suggested parameters
                result_metric, _ = simulate_a_life(args) # We only need the metric here
                print(f"Trial {i + 1} result (discounted_utility): {result_metric}")

                # Complete the trial with the observed metric
                vizier_client.complete_trial({
                    'name': trial.name,
                    'final_measurement': {
                        'metrics': [{'metric_id': 'discounted_utility', 'value': result_metric}]
                    }
                })
            except Exception as e:
                print(f"Error during trial {i + 1}: {e}")
                # Optionally mark the trial as infeasible
                try:
                    vizier_client.complete_trial({
                        'name': trial.name,
                        'trial_infeasible': True,
                        'infeasible_reason': str(e)
                    })
                except Exception as complete_e:
                     print(f"Error completing trial {i + 1} as infeasible: {complete_e}")


        # --- Process and Plot Best Trial (if requested) ---
        if args.plot_best:
            print("\n--- Finding and Processing Optimal Trial ---")
            try:
                opt_trials_response = vizier_client.list_optimal_trials({'parent': STUDY_NAME})

                if not opt_trials_response.optimal_trials:
                     print("No optimal trials found.")
                     return

                optimal_trial = opt_trials_response.optimal_trials[0]
                optimal_parameters = {p.parameter_id: p.value for p in optimal_trial.parameters}
                optimal_metric = optimal_trial.final_measurement.metrics[0].value

                print(f"Optimal trial found with metric value: {optimal_metric}")
                print(f"Optimal parameters: {optimal_parameters}")

                # Update args with optimal parameters
                for param_id, value in optimal_parameters.items():
                    setattr(args, param_id, value)

                # Rerun simulation with optimal parameters to get the full DataFrame
                _, df_optimal = simulate_a_life(args)

                # Plot results
                fig = px.line(df_optimal, x=df_optimal.index, y=df_optimal.columns,
                              title=f'Financial Simulation (Optimal Trial - Metric: {optimal_metric:.0f})')
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
                print(f"Optimal trial plot uploaded to gs://{args.bucket_name}/{file_name}")

            except Exception as e:
                print(f"Error processing or plotting optimal trial: {e}")

    # --- Run a Single Simulation (if num_trials <= 1) ---
    else:
        print("\n--- Running Single Simulation ---")
        try:
            # Run simulation with default/provided args
            result_metric, df_single = simulate_a_life(args)
            print(f"Single simulation result (discounted_utility): {result_metric}")

            # Plot results
            fig = px.line(df_single, x=df_single.index, y=df_single.columns,
                          title='Financial Simulation (Single Run)')
            fig.update_xaxes(title_text='Year')
            fig.update_yaxes(title_text='Value')

            # Save plot to GCS
            file_name = f'{args.file_name}_single_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
            temp_file_path = f"/tmp/{file_name}"
            fig.write_html(temp_file_path)

            storage_client = storage.Client()
            bucket = storage_client.bucket(args.bucket_name)
            blob = bucket.blob(file_name)
            blob.upload_from_filename(temp_file_path)
            os.remove(temp_file_path) # Clean up temp file
            print(f"Single simulation plot uploaded to gs://{args.bucket_name}/{file_name}")

        except Exception as e:
            print(f"Error during single simulation run: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run financial simulation with Vizier optimization.")

    # --- General & Simulation Arguments ---
    parser.add_argument("--bucket_name", required=True, help="GCS bucket name to save results.")
    parser.add_argument("--file_name", default="sim_results", help="Base name for output files.")
    parser.add_argument("--start_year", type=int, default=2024, help="Simulation start year.")
    parser.add_argument("--final_year", type=int, default=2074, help="Simulation end year.")
    parser.add_argument("--retirement_year", type=int, default=2054, help="Year of retirement.")

    # --- Initial Capital Arguments ---
    parser.add_argument("--starting_cash", type=float, default=25000, help="Initial cash on hand.")
    parser.add_argument("--fixed_interest_capital", type=float, default=1000, help="Initial capital in fixed interest account.")
    parser.add_argument("--NSI_capital", type=float, default=50000, help="Initial capital in NSI account.")
    parser.add_argument("--pension_capital", type=float, default=250000, help="Initial pension capital.")
    parser.add_argument("--ISA_capital", type=float, default=200000, help="Initial ISA capital.")
    parser.add_argument("--GIA_capital", type=float, default=600000, help="Initial GIA capital.")

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
    parser.add_argument("--non_linear_utility", type=float, default=0.95, help="Exponent for non-linear utility calculation.")
    parser.add_argument("--utility_discount_rate", type=float, default=0.02, help="Discount rate for calculating net present value of utility.")

    # --- Vizier Specific Arguments ---
    parser.add_argument("--num_trials", type=int, default=11, help="Number of Vizier trials to run (set to 1 for a single simulation).")
    parser.add_argument("--plot_best", type=bool, default=True, help="Whether to run and plot the best trial found by Vizier.")

    # --- Utility Parameters (Default values, potentially overridden by Vizier) ---
    # These arguments are added here so they exist in the args namespace.
    # Vizier will suggest values for these during optimization.
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

    run_vizier_study(args)