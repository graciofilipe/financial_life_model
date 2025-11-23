# Financial Life Model

## Project Overview
This project is a Python-based simulation engine designed to model personal financial progression over decades, specifically tailored to **UK tax and pension rules (2025/26)**.

**Core Objective:** The primary goal is not just to maximize "Net Worth" but to maximize **"Lifetime Utility"**. The simulation treats personal finance as an optimization problem, aiming to smooth consumption over the user's life. It helps users determine the optimal spending path that balances current enjoyment with future security, penalizing volatile lifestyle changes.

The project supports two modes of operation:
1.  **Interactive Web Application:** Built with Streamlit for real-time configuration and **Scenario Comparison (A vs B)**.
2.  **Command Line Interface (CLI):** For headless execution, optimized with **Parallel Monte Carlo** simulations, with results saved to Google Cloud Storage (GCS).

## Core Concepts

*   **Utility Function:** Uses a non-linear utility function (`spending ^ exponent`, where `exponent < 1`, default `0.99`) to model diminishing marginal returns. Users can also configure the **Failure Penalty Exponent** to control how harshly bankruptcy is penalized (Linear vs Quadratic).
*   **Monte Carlo Simulation:** The engine can run hundreds of probabilistic scenarios with randomized investment returns (`Normal(mean, std_dev)`). This generates **"Cones of Uncertainty"** for both Total Assets and Utility Value, visualizing the range of possible outcomes rather than a single deterministic path. Parallelized using `joblib` for performance.
*   **Scenario Comparison:** Run two distinct financial plans side-by-side to visualize the trade-offs (e.g., aggressively paying into a pension vs. keeping cash liquid).
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
*   **Visualization:** Plotly (Fan Charts for Monte Carlo, Overlay Charts for Comparison)
*   **Cloud Integration:** Google Cloud Storage (via `google-cloud-storage`)
*   **Parallelism:** `joblib` for multi-core Monte Carlo execution.
*   **Testing:** `pytest` suite.
*   **Containerization:** Docker

## Key Files & Directories

*   `streamlit_app.py`: The interactive frontend. Includes controls for Scenario A/B, Monte Carlo settings, and overlay visualization.
*   `financial_life/`: Core simulation package.
    *   `simulate_main.py`: CLI entry point and **Monte Carlo Engine**. Handles parallel execution and GCS upload.
    *   `simulate_funs.py`: The main simulation loop (`simulate_a_life`). Integrates all components.
    *   `uk_gov.py`: **Tax Engine**. Encapsulates 2025/26 UK rules (Income Tax bands, NI thresholds, Tiered CGT, Pension Taper).
    *   `investments_and_savings.py`: Logic for asset classes (ISA, GIA, Pension, Fixed Interest) and their specific growth/tax behaviors.
    *   `human.py`: Represents the agent (`Human`), tracking cash, accumulating utility, and managing living costs/salary.
    *   `aux_funs.py`: Helper utilities.
*   `tests/`: Unit test suite.
*   `Dockerfile`: Defines the container image for deployment.

## Setup & Usage

### 1. Installation
Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r financial_life/requirements.txt
pip install pytest # For testing
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
python -m financial_life.simulate_main --bucket_name=<your-gcs-bucket> --monte_carlo_sims=100 [options]
```
Use `python -m financial_life.simulate_main --help` to see all available parameters.

### 4. Testing
Run the unit test suite:

```bash
python -m pytest
```

### 5. Docker Build
To build the container image:

```bash
docker build -t financial-life-model .
```

## Development Conventions
*   **Architecture:** Core simulation logic is decoupled from the presentation layer (`streamlit_app.py`).
*   **Configuration:** Simulation parameters are passed as a namespace object (mimicking `argparse` output) to the core logic, ensuring consistency between CLI and UI execution.
*   **Outputs:** The simulation produces a Pandas DataFrame of year-by-year results and Plotly figures, which are rendered in the UI or saved as artifacts (CSV/HTML) in GCS.
*   **Logging:** Standard Python `logging` is used.