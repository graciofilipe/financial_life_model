# Financial Life Model

## Project Overview
This project is a Python-based simulation engine designed to model personal financial progression over decades, specifically tailored to UK tax and pension rules. 

**Core Objective:** The primary goal is not just to maximize "Net Worth" but to maximize **"Lifetime Utility"**. The simulation treats personal finance as an optimization problem, aiming to smooth consumption over the user's life. It helps users determine the optimal spending path that balances current enjoyment with future security, penalizing volatile lifestyle changes.

The project supports two modes of operation:
1.  **Interactive Web Application:** Built with Streamlit for real-time configuration and visualization.
2.  **Command Line Interface (CLI):** For headless execution, commonly used for batch processing or cloud deployment, with results saved to Google Cloud Storage (GCS).

## Core Concepts

*   **Utility Function:** Uses a non-linear utility function (`spending ^ exponent`, where `exponent < 1`, default `0.99`) to model diminishing marginal returns. Users can also configure the **Failure Penalty Exponent** to control how harshly bankruptcy is penalized (Linear vs Quadratic).
*   **Monte Carlo Simulation:** The engine can run hundreds of probabilistic scenarios with randomized investment returns (`Normal(mean, std_dev)`). This generates **"Cones of Uncertainty"** for both Total Assets and Utility Value, visualizing the range of possible outcomes rather than a single deterministic path.
*   **Stress Testing:** Allows users to simulate specific adverse events, such as a **Market Crash** (e.g., -20% drop) exactly at the year of retirement (Sequence of Returns Risk).
*   **Lifestyling:** Models changing spending needs in later life. Users can define a "Slow Down Year" (e.g., age 80) after which real-term living costs typically decrease ("Slow-Go" phase).
*   **State Pension:** Fully integrates the UK State Pension as a guaranteed, taxable income stream starting at a configurable year.
*   **Discounting:** Future utility is discounted (`utility_discount_rate`) to reflect time preference—happiness today is valued slightly higher than happiness in the distant future.
*   **Volatility Penalty:** A specific metric (`sigma_ut`) penalizes fluctuations in spending. The model explicitly prefers a stable standard of living over a "boom and bust" lifecycle.
*   **Real Values:** All monetary inputs and growth rates are **Real** (inflation-adjusted). A 0% inflation baseline is assumed, meaning "3% growth" represents 3% real growth in purchasing power.

## Tech Stack
*   **Language:** Python 3.12+
*   **Frontend:** Streamlit
*   **Data Analysis:** Pandas, NumPy, NumPy-Financial
*   **Visualization:** Plotly (Fan Charts for Monte Carlo)
*   **Cloud Integration:** Google Cloud Storage (via `google-cloud-storage`)
*   **Containerization:** Docker

## Key Files & Directories

*   `streamlit_app.py`: The interactive frontend. Includes controls for Monte Carlo settings (Sims, Volatility), Stress Testing (Crash %), State Pension, and advanced Utility parameters.
*   `financial_life/`: Core simulation package.
    *   `simulate_main.py`: CLI entry point and **Monte Carlo Engine**. It orchestrates single or multiple runs and aggregates probabilistic results.
    *   `simulate_funs.py`: The main simulation loop (`simulate_a_life`). It calculates year-by-year cash flows, applies the utility function, handles gains harvesting, and enforces the "Buffer" strategy.
    *   `human.py`: Represents the agent (`Human`), tracking cash, accumulating utility, and managing living costs (including One-Off Expenses and Lifestyling).
    *   `uk_gov.py`: Encapsulates UK government rules (Income Tax bands, NI, Capital Gains, **Tapered Annual Allowance** for pensions). This ensures the optimization is grounded in legal reality.
    *   `investments_and_savings.py`: Logic for asset classes (ISA, GIA, Pension, Fixed Interest) and their specific growth/tax behaviors. Supports annual return overrides for stochastic simulations.
    *   `setup_world.py`: Configuration for the economic environment.
*   `Dockerfile`: Defines the container image for deployment.

## Setup & Usage

### 1. Installation
Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r financial_life/requirements.txt
```

### 2. Running the Web App (Interactive)
To start the local development server:

```bash
streamlit run streamlit_app.py
```
The app will be accessible at `http://localhost:8501`.

### 3. Running via CLI (Headless)
To run the simulation without the UI (requires GCS credentials):

```bash
python financial_life/simulate_main.py --bucket_name=<your-gcs-bucket> --monte_carlo_sims=100 [options]
```
Use `python financial_life/simulate_main.py --help` to see all available parameters.

### 4. Docker Build
To build the container image:

```bash
docker build -t financial-life-model .
```

## Development Conventions
*   **Architecture:** Core simulation logic is decoupled from the presentation layer (`streamlit_app.py`).
*   **Configuration:** Simulation parameters are passed as a namespace object (mimicking `argparse` output) to the core logic, ensuring consistency between CLI and UI execution.
*   **Outputs:** The simulation produces a Pandas DataFrame of year-by-year results and Plotly figures, which are rendered in the UI or saved as artifacts (CSV/HTML) in GCS.
*   **Logging:** Standard Python `logging` is used. The CLI defaults to `INFO` level, while the Streamlit app allows user selection of log level.
