# Financial Life Model (UK)

A sophisticated Python-based simulation engine for modeling personal finance over decades, specifically tailored to **UK tax and pension rules**. Unlike standard calculators, it optimizes for **Lifetime Utility**, smoothing consumption to prefer stability over boom-and-bust cycles.

## Features

*   **UK Tax Engine (2025/26):**
    *   **Income Tax:** Personal Allowance taper, all bands (Basic/Higher/Additional).
    *   **National Insurance:** Exact thresholds (PT £12,570 / UEL £50,270).
    *   **Capital Gains Tax:** Tiered rates (18% Basic / 24% Higher) based on total taxable income.
    *   **Pensions:** Annual Allowance tapering for high earners, 25% Tax-Free Lump Sum (PCLS).
*   **Scenario Comparison:** Run two scenarios (A vs B) side-by-side to visualize the impact of different strategies (e.g., "Retire Early" vs "Work Longer").
*   **Monte Carlo Simulation:** Model market volatility to generate "Cones of Uncertainty" for future wealth.
*   **Lifestyling:** Simulate changing spending needs (e.g., "Go-Go" vs "Slow-Go" retirement phases).
*   **Stress Testing:** Simulate specific market crashes at critical moments (Sequence of Returns Risk).

## Setup

1.  **Clone & Install:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    python -m venv .venv
    source .venv/bin/activate
    pip install -r financial_life/requirements.txt
    pip install pytest  # For running tests
    ```

## Usage

### 1. Interactive Web App (Recommended)
Run the Streamlit dashboard to configure and compare scenarios visually:

```bash
streamlit run streamlit_app.py
```
*   **Sidebar:** Configure parameters for Scenario A and B independently.
*   **Global Settings:** Set shared Monte Carlo runs and timeline.
*   **Results:** View comparative metrics and overlay charts for Assets, Utility, and Cash.

### 2. Command Line (Headless/Batch)
Run the core engine directly, useful for cloud jobs or batch processing. Results are saved to Google Cloud Storage (GCS).

```bash
python -m financial_life.simulate_main --bucket_name=<your-bucket> --monte_carlo_sims=100
```
*Use `python -m financial_life.simulate_main --help` for all flags.*

### 3. Testing
The project includes a robust unit test suite using `pytest`.

```bash
python -m pytest
```

## Project Structure

*   `financial_life/`
    *   `uk_gov.py`: The TaxMan class (Income Tax, NI, CGT, Pensions).
    *   `investments_and_savings.py`: Asset classes (ISA, GIA, Pension, Fixed Interest).
    *   `human.py`: The agent (Utility, Salary, Living Costs).
    *   `simulate_funs.py`: Core simulation loop and tax integration.
    *   `simulate_main.py`: CLI entry point and Monte Carlo engine.
*   `streamlit_app.py`: Interactive frontend.
*   `tests/`: Unit tests for all core modules.

## Docker
To build and run the containerized application:

```bash
docker build -t financial-life-model .
docker run -p 8501:8501 financial-life-model
```
