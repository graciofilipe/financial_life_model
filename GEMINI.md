# Financial Life Model

## Project Overview
This project is a Python-based simulation engine designed to model personal financial progression over decades, specifically tailored to UK tax and pension rules. 

**Core Objective:** The primary goal is not just to maximize "Net Worth" but to maximize **"Lifetime Utility"**. The simulation treats personal finance as an optimization problem, aiming to smooth consumption over the user's life. It helps users determine the optimal spending path that balances current enjoyment with future security, penalizing volatile lifestyle changes.

The project supports two modes of operation:
1.  **Interactive Web Application:** Built with Streamlit for real-time configuration and visualization.
2.  **Command Line Interface (CLI):** For headless execution, commonly used for batch processing or cloud deployment, with results saved to Google Cloud Storage (GCS).

## Core Concepts

*   **Utility Function:** Uses a non-linear utility function (`spending ^ exponent`, where `exponent < 1`, default `0.99`) to model diminishing marginal returns. The first £1000 spent contributes more to happiness than the £1000 spent after £50k.
*   **Discounting:** Future utility is discounted (`utility_discount_rate`) to reflect time preference—happiness today is valued slightly higher than happiness in the distant future.
*   **Volatility Penalty:** A specific metric (`sigma_ut`) penalizes fluctuations in spending. The model explicitly prefers a stable standard of living over a "boom and bust" lifecycle.
*   **Real Values:** All monetary inputs and growth rates are **Real** (inflation-adjusted). A 0% inflation baseline is assumed, meaning "3% growth" represents 3% real growth in purchasing power.
*   **Optimization:** The user "tunes" three key parameters (`baseline_utility`, `utility_linear_rate`, `utility_exp_rate`) to define a spending curve. The simulation then tests this curve against realistic financial constraints (taxes, asset yields) to see if it is sustainable and optimal.

## Tech Stack
*   **Language:** Python 3.12+
*   **Frontend:** Streamlit
*   **Data Analysis:** Pandas, NumPy, NumPy-Financial
*   **Visualization:** Plotly
*   **Cloud Integration:** Google Cloud Storage (via `google-cloud-storage`)
*   **Containerization:** Docker

## Key Files & Directories

*   `streamlit_app.py`: The interactive frontend. Allows users to adjust "Utility Parameters" (spending curve) and "Financial Assumptions" to visualize the impact on their lifetime utility metric.
*   `financial_life/`: Core simulation package.
    *   `simulate_main.py`: CLI entry point. orchestrates the simulation and metric calculation.
    *   `simulate_funs.py`: The main simulation loop (`simulate_a_life`). It calculates year-by-year cash flows, applies the utility function, and enforces the "Buffer" strategy.
    *   `human.py`: Represents the agent (`Human`), tracking cash, accumulating utility, and managing living costs.
    *   `uk_gov.py`: Encapsulates UK government rules (Income Tax bands, NI, Capital Gains, **Tapered Annual Allowance** for pensions). This ensures the optimization is grounded in legal reality.
    *   `investments_and_savings.py`: Logic for asset classes (ISA, GIA, Pension, Fixed Interest) and their specific growth/tax behaviors.
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
python financial_life/simulate_main.py --bucket_name=<your-gcs-bucket> [options]
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
