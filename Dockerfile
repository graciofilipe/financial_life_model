# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# --- Copy Simulation Code ---
# Copy the entire 'financial_life' directory containing your simulation scripts
# into the container under the working directory.
COPY financial_life/ ./financial_life/
COPY streamlit_app.py .

# --- Install Dependencies ---
# Copy the full requirements file for the simulation
COPY financial_life/requirements.txt .

# Install Python dependencies for Flask AND the simulation
# Using --no-cache-dir reduces image size
RUN pip install --no-cache-dir --upgrade pip
# Flask is no longer needed
RUN pip install --no-cache-dir -r requirements.txt # Install simulation AND Streamlit dependencies (streamlit is in requirements.txt)

# Make Streamlit's default port available

# Optional: Set PYTHONPATH if your simulation code uses relative imports across modules
ENV PYTHONPATH=/app

# Run streamlit_app.py when the container launches
# Use shell form to allow $PORT substitution
ENTRYPOINT streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
