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
    
    # --- State Pension ---
    st.subheader("State Pension")
    in_state_pension_start_year = st.number_input("State Pension Start Year", value=int(in_retirement_year) + 10, help="Year when State Pension starts (e.g., 2060).")
    in_state_pension_amount = st.number_input("State Pension Amount (£/yr)", value=11502.0, format="%.2f", help="Annual State Pension amount.")

    # --- One-Off Expenses ---
    in_one_off_expenses_str = st.text_area("One-Off Expenses (JSON)", value="{}", help="Enter a JSON dictionary mapping years to amounts. E.g., {\"2030\": 50000, \"2040\": 20000}")

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
    in_slow_down_year = st.number_input("Slow Down Year (Lifestyling)", value=int(in_retirement_year) + 20, help="Year when spending slows down (e.g., age 75/80).")
    in_living_costs_rate_post_slow_down = st.number_input("Living Costs Rate (Post-Slow Down)", value=0.0, format="%.4f", step=0.001, help="Rate after the slow down year (e.g., 0.0 for flat real spending).")
    in_salary_growth_rate = st.number_input("Salary Growth Rate", value=0.01, format="%.4f", step=0.001, help=rate_help_text)
    in_salary_growth_stop_year = st.number_input("Salary Growth Stop Year (Plateau)", value=int(in_retirement_year), help="Year after which salary stops growing. Set to Retirement Year for continuous growth.")
    in_salary_post_plateau_growth_rate = st.number_input("Salary Post-Plateau Rate", value=0.0, format="%.4f", step=0.001, help="Annual rate after the stop year. Use negative values (e.g. -0.01) for salary decline.")

    # --- Employment & Pension Contributions (%) ---
    st.subheader("Employment & Pension Contributions (%)")
    contrib_help_text = "Enter as a decimal (e.g., 0.07 for 7%)"
    in_employee_pension_contributions_pct = st.number_input("Employee Pension Contributions Pct", value=0.07, format="%.4f", step=0.001, help=contrib_help_text)
    in_employer_pension_contributions_pct = st.number_input("Employer Pension Contributions Pct", value=0.07, format="%.4f", step=0.001, help=contrib_help_text)
    in_pension_lump_sum_spread_years = st.number_input("Pension Lump Sum Spread Years", value=1, min_value=1, max_value=20, help="Number of years to spread the tax-free lump sum over.")

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
    in_volatility_penalty = st.number_input("Volatility Penalty", value=100000.0, format="%.0f", step=1000.0, help="Penalty factor for utility volatility (stdev/mean) in the final metric.")
    in_failure_penalty_exponent = st.number_input("Failure Penalty Exponent", value=2.0, format="%.1f", step=0.1, help="Exponent for unpaid costs penalty (1.0=Linear, 2.0=Quadratic). Lower reduces skew from bankruptcy.")

    # --- Stress Testing ---
    st.subheader("Stress Testing")
    in_stress_test_market_crash_pct = st.slider("Market Crash at Retirement (%)", min_value=0.0, max_value=0.5, value=0.0, step=0.05, help="Simulate a market drop in the year you retire.")

    # --- Monte Carlo Simulation ---
    st.subheader("Monte Carlo Simulation")
    in_monte_carlo_sims = st.slider("Number of Simulations", min_value=1, max_value=100, value=1, help="Number of random scenarios to run. >1 enables Monte Carlo mode.")
    in_investment_volatility = st.number_input("Investment Volatility (Std Dev)", value=0.15, format="%.2f", step=0.01, help="Standard deviation of annual returns (e.g., 0.15 for 15%).")

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
        # --- Parse One-Off Expenses ---
        import json
        try:
            one_off_expenses_dict = json.loads(in_one_off_expenses_str)
            # Basic type check: keys should be convertible to int, values to float
            for k, v in one_off_expenses_dict.items():
                int(k)
                float(v)
        except ValueError as e:
            st.sidebar.error(f"Invalid One-Off Expenses format. Must be valid JSON with year keys and numeric amounts. Error: {e}")
            st.stop()
        except Exception as e:
            st.sidebar.error(f"Error parsing One-Off Expenses: {e}")
            st.stop()

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
            "slow_down_year": int(in_slow_down_year),
            "living_costs_rate_post_slow_down": in_living_costs_rate_post_slow_down,
            "salary_growth_rate": in_salary_growth_rate,
            "salary_growth_stop_year": int(in_salary_growth_stop_year),
            "salary_post_plateau_growth_rate": in_salary_post_plateau_growth_rate,
            "base_living_cost": in_base_living_cost,
            "base_salary": in_base_salary,
            "state_pension_start_year": int(in_state_pension_start_year),
            "state_pension_amount": in_state_pension_amount,
            "employee_pension_contributions_pct": in_employee_pension_contributions_pct,
            "employer_pension_contributions_pct": in_employer_pension_contributions_pct,
            "pension_lump_sum_spread_years": int(in_pension_lump_sum_spread_years),
            "buffer_multiplier": in_buffer_multiplier,
            "utility_baseline": in_utility_baseline,
            "utility_linear_rate": in_utility_linear_rate,
            "utility_exp_rate": in_utility_exp_rate,
            "non_linear_utility": in_non_linear_utility,
            "utility_discount_rate": in_utility_discount_rate,
            "volatility_penalty": in_volatility_penalty,
            "failure_penalty_exponent": in_failure_penalty_exponent,
            "stress_test_market_crash_pct": in_stress_test_market_crash_pct,
            "monte_carlo_sims": in_monte_carlo_sims,
            "investment_volatility": in_investment_volatility,
            "log_level": in_log_level,
            "one_off_expenses": one_off_expenses_dict,
            # Pass the checkbox state to the simulation function's save_debug_data param.
            "save_debug_data": in_show_debug_data
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
                
                if in_monte_carlo_sims > 1:
                    st.metric("Average Utility Metric", f"{metric:.2f}")
                    
                    st.subheader("Monte Carlo Analysis")
                    if plots and 'Monte_Carlo_Assets' in plots:
                        st.plotly_chart(plots['Monte_Carlo_Assets'], use_container_width=True)
                    
                    st.subheader("Simulation Statistics (Total Assets)")
                    st.dataframe(df)
                    
                else:
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