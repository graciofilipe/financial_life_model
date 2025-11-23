import streamlit as st
import argparse
import logging
import pandas as pd
import sys
import os
import json
import plotly.graph_objects as go
import plotly.express as px

# --- Import Simulation Function ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from financial_life.simulate_main import run_simulation_and_get_results
except ImportError as e:
    st.error(f"Could not import simulation function. Error: {e}")
    st.stop()

# --- Basic Logging ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - StreamlitApp - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

st.set_page_config(layout="wide", page_title="Financial Life: Scenario Comparison")

st.title("Financial Life Simulation & Comparison")
st.markdown("Define two scenarios (A and B) in the sidebar to compare outcomes. Results and overlays will appear below.")

# --- Helper Function: Input Widgets ---
def get_scenario_inputs(prefix, default_overrides={}):
    """
    Generates Streamlit input widgets for a single scenario.
    Returns a dictionary of parameter values.
    """
    
    # Helper for unique keys
    k = lambda s: f"{prefix}_{s}"
    
    st.markdown(f"### {prefix} Configuration")
    
    # --- Initial Capital ---
    st.caption("Initial Capital (£)")
    starting_cash = st.number_input("Starting Cash", value=default_overrides.get('starting_cash', 5000), key=k("starting_cash"))
    pension_capital = st.number_input("Pension Capital", value=default_overrides.get('pension_capital', 150000), key=k("pension_capital"))
    isa_capital = st.number_input("ISA Capital", value=default_overrides.get('isa_capital', 150000), key=k("isa_capital"))
    gia_capital = st.number_input("GIA Capital", value=default_overrides.get('gia_capital', 500000), key=k("gia_capital"))
    nsi_capital = st.number_input("NSI Capital", value=default_overrides.get('nsi_capital', 50000), key=k("nsi_capital"))
    fixed_interest_capital = st.number_input("Fixed Interest Capital", value=default_overrides.get('fixed_interest_capital', 0), key=k("fixed_interest_capital"))
    
    gia_units = st.number_input("GIA Initial Units", value=100.0, format="%.4f", key=k("gia_units"))
    gia_price = st.number_input("GIA Avg Buy Price", value=0.0, format="%.4f", help="Leave 0 to auto-calc", key=k("gia_price"))
    gia_price_val = gia_price if gia_price > 0 else None

    # --- Base Values ---
    st.caption("Base Values")
    base_living_cost = st.number_input("Base Living Cost", value=20000.0, key=k("base_cost"))
    base_salary = st.number_input("Base Salary", value=100000.0, key=k("base_salary"))
    
    # --- State Pension ---
    st.caption("State Pension")
    state_pension_start = st.number_input("Start Year", value=2060, key=k("sp_start")) # Adjusted default
    state_pension_amt = st.number_input("Amount (£/yr)", value=11502.0, key=k("sp_amt"))

    # --- One-Off Expenses ---
    one_off_json = st.text_area("One-Off Expenses (JSON)", value="{}", key=k("one_off"), help='e.g. {"2035": 20000}')

    # --- Growth Rates ---
    st.caption("Growth Rates (Decimals)")
    r_pension = st.number_input("Pension Growth", value=0.02, step=0.001, format="%.4f", key=k("r_pension"))
    r_isa = st.number_input("ISA Growth", value=0.02, step=0.001, format="%.4f", key=k("r_isa"))
    r_gia = st.number_input("GIA Growth", value=0.02, step=0.001, format="%.4f", key=k("r_gia"))
    r_salary = st.number_input("Salary Growth", value=0.01, step=0.001, format="%.4f", key=k("r_salary"))
    r_living_pre = st.number_input("Living Cost Growth (Pre-Ret)", value=0.02, step=0.001, format="%.4f", key=k("r_liv_pre"))
    r_living_post = st.number_input("Living Cost Growth (Post-Ret)", value=0.04, step=0.001, format="%.4f", key=k("r_liv_post"))
    
    # --- Strategy ---
    st.caption("Strategy & Utility")
    buffer_mult = st.number_input("Buffer Multiplier", value=1.2, step=0.1, key=k("buffer"))
    util_baseline = st.number_input("Utility Baseline", value=30000.0, key=k("util_base"))
    stress_crash = st.slider("Crash at Retirement (%)", 0.0, 0.5, 0.0, 0.05, key=k("crash"))

    return {
        "starting_cash": starting_cash,
        "pension_capital": pension_capital,
        "ISA_capital": isa_capital,
        "GIA_capital": gia_capital,
        "NSI_capital": nsi_capital,
        "fixed_interest_capital": fixed_interest_capital,
        "GIA_initial_units": gia_units,
        "GIA_initial_average_buy_price": gia_price_val,
        "base_living_cost": base_living_cost,
        "base_salary": base_salary,
        "state_pension_start_year": int(state_pension_start),
        "state_pension_amount": state_pension_amt,
        "one_off_expenses": one_off_json,
        "pension_growth_rate": r_pension,
        "ISA_growth_rate": r_isa,
        "GIA_growth_rate": r_gia,
        "salary_growth_rate": r_salary,
        "living_costs_rate_pre_retirement": r_living_pre,
        "living_costs_rate_post_retirement": r_living_post,
        "buffer_multiplier": buffer_mult,
        "utility_baseline": util_baseline,
        "stress_test_market_crash_pct": stress_crash,
        # --- Fixed/Hidden/Advanced Defaults (to simplify UI for now) ---
        "fixed_interest_rate": 0.02,
        "NSI_interest_rate": 0.02,
        "slow_down_year": 2075, # Default far future
        "living_costs_rate_post_slow_down": 0.0,
        "salary_growth_stop_year": 2055, # Matches default retirement
        "salary_post_plateau_growth_rate": 0.0,
        "employee_pension_contributions_pct": 0.07,
        "employer_pension_contributions_pct": 0.07,
        "pension_lump_sum_spread_years": 1,
        "utility_linear_rate": 0.0,
        "utility_exp_rate": 0.005,
        "non_linear_utility": 0.99,
        "utility_discount_rate": 0.001,
        "volatility_penalty": 100000.0,
        "failure_penalty_exponent": 2.0
    }

# --- Sidebar Layout ---
with st.sidebar.form(key='main_form'):
    st.header("Global Settings")
    bucket_name = st.text_input("GCS Bucket", value="", help="Required for saving artifacts")
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input("Start Year", 2025, 2050, 2025)
    with col2:
        final_year = st.number_input("Final Year", 2030, 2100, 2074)
    
    ret_year = st.number_input("Retirement Year", 2025, 2100, 2055)
    
    # Monte Carlo
    mc_sims = st.slider("Monte Carlo Sims", 1, 50, 1, help="Runs multiple probabilistic scenarios")
    volatility = st.number_input("Investment Volatility (Std Dev)", value=0.15, step=0.01, format="%.2f", help="Annual standard deviation (0.15 = 15%)")
    
    st.markdown("---")
    st.header("Scenario Config")
    
    tab_a, tab_b = st.tabs(["Scenario A", "Scenario B"])
    
    with tab_a:
        params_a_dict = get_scenario_inputs("A")
    
    with tab_b:
        # Optional: Preset defaults to differentiate B slightly?
        params_b_dict = get_scenario_inputs("B", default_overrides={'starting_cash': 10000})

    submit_btn = st.form_submit_button("Compare Scenarios")

# --- Execution Logic ---
if submit_btn:
    if not bucket_name:
        st.error("Please provide a GCS Bucket Name.")
        st.stop()

    # Parse JSONs
    try:
        params_a_dict['one_off_expenses'] = json.loads(params_a_dict['one_off_expenses'])
        params_b_dict['one_off_expenses'] = json.loads(params_b_dict['one_off_expenses'])
    except Exception as e:
        st.error(f"JSON Parse Error: {e}")
        st.stop()

    # Add Global Params to both
    global_params = {
        "bucket_name": bucket_name,
        "start_year": int(start_year),
        "final_year": int(final_year),
        "retirement_year": int(ret_year),
        "monte_carlo_sims": mc_sims,
        "investment_volatility": volatility,
        "file_name": "sim", # Base name
        "log_level": "INFO",
        "save_debug_data": False
    }
    
    # Construct Namespace objects
    full_params_a = {**params_a_dict, **global_params, "file_name": "sim_A"}
    full_params_b = {**params_b_dict, **global_params, "file_name": "sim_B"}
    
    ns_a = argparse.Namespace(**full_params_a)
    ns_b = argparse.Namespace(**full_params_b)

    # Run Simulations
    with st.spinner("Running Scenario A..."):
        metric_a, df_a, plots_a, _ = run_simulation_and_get_results(ns_a)
    
    with st.spinner("Running Scenario B..."):
        metric_b, df_b, plots_b, _ = run_simulation_and_get_results(ns_b)

    # --- Results Display ---
    st.markdown("## Comparison Results")
    
    # Metrics Row
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Metric A (Utility)", f"{metric_a:,.0f}")
    m_col2.metric("Metric B (Utility)", f"{metric_b:,.0f}")
    delta = metric_b - metric_a
    m_col3.metric("Difference (B - A)", f"{delta:,.0f}", delta_color="normal")

    # --- Overlays ---
    st.subheader("Visual Comparisons")
    
    if df_a is not None and df_b is not None:
        # 1. Total Assets Overlay
        fig_assets = go.Figure()
        fig_assets.add_trace(go.Scatter(x=df_a.index, y=df_a['Total Assets'], mode='lines', name='Scenario A', line=dict(color='blue')))
        fig_assets.add_trace(go.Scatter(x=df_b.index, y=df_b['Total Assets'], mode='lines', name='Scenario B', line=dict(color='orange', dash='dash')))
        fig_assets.update_layout(title="Total Assets Comparison", xaxis_title="Year", yaxis_title="Value (£)")
        st.plotly_chart(fig_assets, use_container_width=True)

        # 2. Utility Overlay
        fig_util = go.Figure()
        fig_util.add_trace(go.Scatter(x=df_a.index, y=df_a['Utility Value'], mode='lines', name='Scenario A', line=dict(color='green')))
        fig_util.add_trace(go.Scatter(x=df_b.index, y=df_b['Utility Value'], mode='lines', name='Scenario B', line=dict(color='red', dash='dash')))
        fig_util.update_layout(title="Utility Value Comparison", xaxis_title="Year", yaxis_title="Utility")
        st.plotly_chart(fig_util, use_container_width=True)

        # 3. Cash Overlay
        fig_cash = go.Figure()
        fig_cash.add_trace(go.Scatter(x=df_a.index, y=df_a['Cash'], mode='lines', name='Scenario A', line=dict(color='teal')))
        fig_cash.add_trace(go.Scatter(x=df_b.index, y=df_b['Cash'], mode='lines', name='Scenario B', line=dict(color='purple', dash='dash')))
        fig_cash.update_layout(title="Liquid Cash Comparison", xaxis_title="Year", yaxis_title="Cash (£)")
        st.plotly_chart(fig_cash, use_container_width=True)

        # Data Tables
        with st.expander("View Scenario A Data"):
            st.dataframe(df_a)
        with st.expander("View Scenario B Data"):
            st.dataframe(df_b)
            
    else:
        st.error("One or both simulations failed to produce data.")

else:
    st.info("Configure scenarios and click 'Compare Scenarios' to run.")
