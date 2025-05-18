import streamlit as st
import argparse # Using argparse to create a Namespace object
import logging
import pandas as pd # Needed for displaying debug data
import sys
import os # Import the os module
import sys # Ensure sys is imported if not already

# --- Import Simulation Function ---
# Assuming 'financial_life' directory is in the same directory as this script (repo root)
project_root = os.path.dirname(os.path.abspath(__file__))

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now try the import
try:
    from financial_life.simulate_main import run_simulation_and_get_results
except ImportError as e:
    # Keep the existing error handling
    st.error(f"Could not import simulation function. Ensure 'financial_life' directory exists relative to the script and the project root is in the Python path. Error: {e}")
    st.stop() # Stop execution if import fails

# --- Basic Logging ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - StreamlitApp - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# --- Page Configuration ---
st.set_page_config(layout="wide")

# --- App Title ---
st.title("Financial Life Simulation")
st.markdown("Configure parameters in the sidebar and click 'Run Simulation'. Results will appear below.")

# --- Sidebar for Inputs ---
st.sidebar.header("Simulation Parameters")

# --- Input Form ---
# Define widgets within the form
with st.sidebar.form(key='simulation_params'):

    # --- General & Simulation Settings ---
    st.subheader("General & Simulation Settings")
    in_bucket_name = st.text_input("GCS Bucket Name (Required)", value="", help="GCS bucket name where results will be saved.")
    in_file_name = st.text_input("Base File Name", value="sim_results_st", help="Base name for output files saved to GCS.")
    in_start_year = st.number_input("Start Year", value=2025, help="Simulation start year.")
    in_final_year = st.number_input("Final Year", value=2074, help="Simulation end year.")
    in_retirement_year = st.number_input("Retirement Year", value=2055, help="Year of retirement.")

    # --- Initial Capital (£) ---
    st.subheader("Initial Capital (£)")
    in_starting_cash = st.number_input("Starting Cash", value=5000, help="Initial cash on hand.")
    in_NSI_capital = st.number_input("NSI Capital", value=50000, help="Initial capital in NSI account.")
    in_pension_capital = st.number_input("Pension Capital", value=150000, help="Initial pension capital.")
    in_ISA_capital = st.number_input("ISA Capital", value=150000, help="Initial ISA capital.")
    in_GIA_capital = st.number_input("GIA Capital (Total Value)", value=500000, help="Initial total value of GIA capital.")
    in_GIA_initial_units = st.number_input("GIA Initial Units", value=100.0, format="%.4f", help="Initial number of units in GIA.")
    in_GIA_initial_average_buy_price = st.number_input("GIA Initial Average Buy Price (Optional)", value=None, format="%.4f", help="Optional: Average buy price per unit. If None, derived from GIA Capital / Units.", placeholder="Optional")
    in_fixed_interest_capital = st.number_input("Fixed Interest Capital", value=0,  help="Initial total value of fixed interest capital.")


    # --- Base Values (£) ---
    st.subheader("Base Values (£)")
    in_base_living_cost = st.number_input("Base Living Cost (Start Year)", value=20000.0, format="%.2f", help="Base living cost amount in the start year.")
    in_base_salary = st.number_input("Base Salary (Year before Start)", value=100000.0, format="%.2f", help="Base gross salary amount in the year before the start year.")

    # --- Annual Rates & Growth (%) ---
    st.subheader("Annual Rates & Growth (%)")
    rate_help_text = "Enter as a decimal (e.g., 0.02 for 2%)"
    in_fixed_interest_rate = st.number_input("Fixed Interest Rate", value=0.02, format="%.4f", step=0.001, help=rate_help_text)
    in_NSI_interest_rate = st.number_input("NSI Interest Rate", value=0.02, format="%.4f", step=0.001, help=rate_help_text)
    in_pension_growth_rate = st.number_input("Pension Growth Rate", value=0.02, format="%.4f", step=0.001, help=rate_help_text)
    in_ISA_growth_rate = st.number_input("ISA Growth Rate", value=0.02, format="%.4f", step=0.001, help=rate_help_text)
    in_GIA_growth_rate = st.number_input("GIA Growth Rate", value=0.02, format="%.4f", step=0.001, help=rate_help_text)
    in_living_costs_rate_pre_retirement = st.number_input("Living Costs Growth Rate (Pre-Retirement)", value=0.02, format="%.4f", step=0.001, help=rate_help_text)
    in_living_costs_rate_post_retirement = st.number_input("Living Costs Growth Rate (Post-Retirement)", value=0.04, format="%.4f", step=0.001, help=rate_help_text)
    in_salary_growth_rate = st.number_input("Salary Growth Rate", value=0.01, format="%.4f", step=0.001, help=rate_help_text)

    # --- Employment & Pension Contributions (%) ---
    st.subheader("Employment & Pension Contributions (%)")
    contrib_help_text = "Enter as a decimal (e.g., 0.07 for 7%)"
    in_employee_pension_contributions_pct = st.number_input("Employee Pension Contributions Pct", value=0.07, format="%.4f", step=0.001, help=contrib_help_text)
    in_employer_pension_contributions_pct = st.number_input("Employer Pension Contributions Pct", value=0.07, format="%.4f", step=0.001, help=contrib_help_text)

    # --- Strategy ---
    st.subheader("Strategy")
    in_buffer_multiplier = st.number_input("Cash Buffer Multiplier", value=1.2, format="%.2f", step=0.1, help="Multiplier for cash buffer based on current year's living costs.")

    # --- Utility Function Parameters ---
    st.subheader("Utility Function Parameters")
    in_utility_baseline = st.number_input("Utility Baseline (£, Start Year)", value=30000.0, format="%.2f", help="Baseline desired utility spending in the start year.")
    in_utility_linear_rate = st.number_input("Utility Linear Rate (£/Year)", value=0.0, format="%.2f", help="Absolute amount (£) to add to baseline utility each year.")
    in_utility_exp_rate = st.number_input("Utility Exponential Rate (%/Year)", value=0.005, format="%.4f", step=0.0001, help=rate_help_text + " for utility growth.")
    in_non_linear_utility = st.number_input("Non-Linear Utility Exponent", value=0.99, format="%.4f", step=0.01, help="Exponent for calculating actual utility from spending (e.g., 0.5 for sqrt).")
    in_utility_discount_rate = st.number_input("Utility Discount Rate (%/Year)", value=0.001, format="%.4f", step=0.0001, help=rate_help_text + " for NPV calculation.")

    # --- Troubleshooting ---
    st.subheader("Troubleshooting")
    in_log_level = st.selectbox("Log Level", options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], index=1, help="Set the logging level for simulation output (shown in app logs).") # Default INFO
    # This checkbox controls *displaying* debug data in Streamlit.
    in_show_debug_data = st.checkbox("Show Debug Data Table", value=False, help="Display the detailed debug DataFrame below the main results.")

    # --- Form Submission ---
    # This button submits all widgets defined within the 'with st.sidebar.form(...)' block
    submitted = st.form_submit_button("Run Simulation")

# --- Simulation Execution and Results Display ---
# This block executes only when the form button is clicked
if submitted:
    logging.info(f"Form submitted. Bucket: '{in_bucket_name}', Show Debug: {in_show_debug_data}")

    # --- Basic Validation ---
    if not in_bucket_name:
        st.sidebar.error("GCS Bucket Name is required.")
        # Stop processing this specific submission
    else:
        # --- Collect Inputs into Dictionary (AFTER validation) ---
        
        params_dict = {
            "bucket_name": in_bucket_name,
            "file_name": in_file_name,
            "start_year": int(in_start_year),
            "final_year": int(in_final_year),
            "retirement_year": int(in_retirement_year),
            "starting_cash": in_starting_cash,
            "fixed_interest_capital": in_fixed_interest_capital,
            "NSI_capital": in_NSI_capital,
            "pension_capital": in_pension_capital,
            "ISA_capital": in_ISA_capital,
            "GIA_capital": in_GIA_capital,
            "GIA_initial_units": in_GIA_initial_units if in_GIA_initial_units is not None else 0.0,
            "GIA_initial_average_buy_price": in_GIA_initial_average_buy_price if in_GIA_initial_average_buy_price is not None else None,
            "fixed_interest_rate": in_fixed_interest_rate,
            "NSI_interest_rate": in_NSI_interest_rate,
            "pension_growth_rate": in_pension_growth_rate,
            "ISA_growth_rate": in_ISA_growth_rate,
            "GIA_growth_rate": in_GIA_growth_rate,
            "living_costs_rate_pre_retirement": in_living_costs_rate_pre_retirement,
            "living_costs_rate_post_retirement": in_living_costs_rate_post_retirement,
            "salary_growth_rate": in_salary_growth_rate,
            "base_living_cost": in_base_living_cost,
            "base_salary": in_base_salary,
            "employee_pension_contributions_pct": in_employee_pension_contributions_pct,
            "employer_pension_contributions_pct": in_employer_pension_contributions_pct,
            "buffer_multiplier": in_buffer_multiplier,
            "utility_baseline": in_utility_baseline,
            "utility_linear_rate": in_utility_linear_rate,
            "utility_exp_rate": in_utility_exp_rate,
            "non_linear_utility": in_non_linear_utility,
            "utility_discount_rate": in_utility_discount_rate,
            "volatility_penalty": 0,
            "log_level": in_log_level,
            # Save debug data to GCS if a bucket name is provided, independent of UI display.
            "save_debug_data": True if in_bucket_name else False,
        }

        # --- Convert Dictionary to Namespace ---
        params_namespace = argparse.Namespace(**params_dict)

        logging.info("Validation passed and parameters collected. Starting simulation run.")
        st.markdown("---") # Add separator

        # --- Run Simulation ---
        with st.spinner("Running simulation... please wait"):
            try:
                # Configure logging level for the simulation run based on input
                log_level_numeric = getattr(logging, params_namespace.log_level.upper(), logging.INFO)
                logging.getLogger().setLevel(log_level_numeric) # Set root logger level
                logging.info(f"Set logging level to {params_namespace.log_level}")

                # Call the simulation function
                metric, df, plots, debug_data = run_simulation_and_get_results(params_namespace)

                # --- Display Results ---
                st.header("Simulation Results")
                st.metric("Final Utility Metric", f"{metric:.2f}")

                st.subheader("Result Data")
                st.dataframe(df)

                st.subheader("Result Plots")
                if plots:
                    plot_order = ["Assets", "Utility", "Living_Costs", "Income_Tax_Summary", "Investment_Flows", "Tax_Details"]
                    displayed_plots = set() # Keep track of plots already displayed

                    # Display plots in the specified order
                    for plot_name in plot_order:
                        if plot_name in plots:
                            fig = plots[plot_name]
                            st.plotly_chart(fig, use_container_width=True)
                            displayed_plots.add(plot_name)
                        else:
                            # Optional: Log or display a warning if an expected plot is missing
                            logging.warning(f"Expected plot '{plot_name}' not found in simulation results.")
                            # st.warning(f"Expected plot '{plot_name}' not found.") # Uncomment to show in UI

                    # Optional: Display any remaining plots not in the defined order
                    for plot_name, fig in plots.items():
                        if plot_name not in displayed_plots:
                            logging.warning(f"Displaying additional plot not in specified order: {plot_name}")
                            st.warning(f"Displaying additional plot: {plot_name}") # Indicate it's an extra plot
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No plots were generated by the simulation.")

                # Display debug data if checkbox checked AND data was returned
                if in_show_debug_data and debug_data is not None:
                    with st.expander("Debug Data"):
                        # Convert list of dicts to DataFrame before displaying
                        st.dataframe(pd.DataFrame(debug_data))
                elif in_show_debug_data and debug_data is None:
                    # Checkbox was ticked, but simulation didn't return debug data
                     st.warning("Debug data was requested, but none was generated/returned by the simulation.")


                logging.info("Simulation and results display completed successfully.")
                st.success(f"Simulation successful. Results potentially saved to GCS bucket '{params_namespace.bucket_name}'.")

            except ImportError as ie:
                 st.error(f"Import Error during simulation call: {ie}.")
                 logging.error(f"Import Error during simulation call: {ie}", exc_info=True)
            except Exception as e:
                st.error(f"An error occurred during the simulation: {e}")
                logging.critical(f"Exception during simulation run: {e}", exc_info=True)

else:
    # Initial state before form submission (or after failed validation)
    st.markdown("---")
    st.info("Adjust parameters in the sidebar and click 'Run Simulation' to start.")
