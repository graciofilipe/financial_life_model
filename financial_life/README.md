# Financial Life Model

This project simulates personal financial progression over several decades, considering income, expenses, investments, taxes, and pensions according to UK rules. The simulation results are visualized using a Streamlit application.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```
2.  **Install dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install --upgrade pip
    pip install -r financial_life/requirements.txt
    ```

## Running the Application

To run the financial simulation locally using the Streamlit interface:

```bash
streamlit run streamlit_app.py
```

The application will open in your web browser. Configure the simulation parameters in the sidebar and click "Configure Simulation" (or similar button name) to run the simulation and view the results.

## Deployment

A `Dockerfile` is included in the repository root for building a container image of the application, suitable for deployment on platforms like Google Cloud Run. It uses the Streamlit application as the entry point.

```bash
# Example build command
docker build -t financial-life-model .

# Example run command (maps container port 8501 to host port 8501)
docker run -p 8501:8501 financial-life-model
```

## Command-Line Execution (Legacy)

The core simulation can still be run via the command line, which saves results directly to Google Cloud Storage:

```bash
python financial_life/simulate_main.py --bucket_name=<your-gcs-bucket> [other arguments...]
```
Run `python financial_life/simulate_main.py --help` to see all available arguments.