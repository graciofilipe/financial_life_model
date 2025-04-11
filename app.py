import os
import subprocess
import json
import shlex # For safely splitting command strings if needed, though list format is preferred
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app
app = Flask(__name__, template_folder='.', static_folder='static') # Serve from root

# --- Simulation Script Path ---
# Assumes your simulation code is in a 'financial_life' subdirectory
SIMULATION_SCRIPT = os.path.join('financial_life', 'simulate_main.py')
PYTHON_EXECUTABLE = 'python' # Or specify a full path if needed, e.g., /usr/local/bin/python

# --- Routes ---

@app.route('/')
def index():
    """Serves the main HTML configuration page."""
    return render_template('index.html')

@app.route('/run_simulation', methods=['POST'])
def run_simulation():
    """
    Receives simulation parameters via POST request, constructs the command,
    and executes the simulation script asynchronously using subprocess.Popen.
    """
    logging.info("Received request to run simulation.")
    try:
        # Get parameters from the JSON body of the POST request
        params = request.get_json()
        if not params:
            logging.error("No parameters received in request body.")
            return jsonify({"status": "error", "message": "No parameters received."}), 400

        logging.info(f"Received parameters: {json.dumps(params)}")

        # --- Construct the command-line arguments ---
        # Start with the Python interpreter and the script path
        cmd = [PYTHON_EXECUTABLE, SIMULATION_SCRIPT]

        # Iterate through the received parameters and add them as arguments
        for key, value in params.items():
            # Handle boolean flags (like --save_debug_data)
            if isinstance(value, bool):
                if value: # Add the flag only if True
                    cmd.append(f"--{key}")
            # Handle other arguments with values
            elif value is not None and value != '': # Add argument if it has a value
                cmd.append(f"--{key}")
                cmd.append(str(value)) # Ensure value is a string for the command line

        logging.info(f"Constructed command: {' '.join(cmd)}") # Log the command for debugging

        # --- Execute the simulation script asynchronously ---
        # Use Popen for non-blocking execution. Redirect stdout/stderr to files or PIPE.
        # Using PIPE allows capturing initial output/errors if needed, but can fill buffers
        # on long processes. For simplicity, let's just launch it.
        # Consider redirecting stdout/stderr to log files within the container for better debugging.
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Optional: Check immediately if the process started correctly (e.g., script not found)
        # This is a basic check; runtime errors within the script won't be caught here.
        # stdout, stderr = process.communicate(timeout=5) # Short timeout for initial check
        # if process.returncode is not None and process.returncode != 0:
        #     logging.error(f"Simulation script failed to start. Return code: {process.returncode}. Stderr: {stderr}")
        #     return jsonify({"status": "error", "message": f"Simulation failed to start: {stderr[:500]}"}), 500

        logging.info(f"Simulation process started with PID: {process.pid}")

        # Return success message immediately
        return jsonify({"status": "success", "message": "Simulation started successfully."}), 200

    except json.JSONDecodeError:
        logging.error("Invalid JSON received.")
        return jsonify({"status": "error", "message": "Invalid JSON format in request."}), 400
    except FileNotFoundError:
         logging.error(f"Simulation script '{SIMULATION_SCRIPT}' or Python executable '{PYTHON_EXECUTABLE}' not found.")
         return jsonify({"status": "error", "message": "Simulation script or Python not found on server."}), 500
    except Exception as e:
        logging.exception("An unexpected error occurred while trying to start the simulation.")
        return jsonify({"status": "error", "message": f"An unexpected server error occurred: {str(e)}"}), 500


# --- Optional: Static files route ---
# @app.route('/static/<path:path>')
# def send_static(path):
#    """Serves static files."""
#    return send_from_directory('static', path)
# --- End Optional ---


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # Use host='0.0.0.0' to be accessible externally within the container network
    app.run(debug=False, host='0.0.0.0', port=port)
