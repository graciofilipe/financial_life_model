# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# --- Copy Simulation Code ---
# Copy the entire 'financial_life' directory containing your simulation scripts
# into the container under the working directory.
COPY financial_life/ ./financial_life/

# --- Copy Application Code ---
COPY app.py .
COPY index.html .
# If you create a 'static' folder later for CSS/JS, uncomment the next line
# COPY static/ ./static/

# --- Install Dependencies ---
# Copy the full requirements file for the simulation
COPY financial_life/requirements.txt .

# Install Python dependencies for Flask AND the simulation
# Using --no-cache-dir reduces image size
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir Flask==2.3.3 # Ensure Flask is installed
RUN pip install --no-cache-dir -r requirements.txt # Install simulation dependencies

# Make port 8080 available (Cloud Run uses the PORT environment variable)
EXPOSE 8080

# Define environment variable (Cloud Run will set this)
ENV PORT=8080
# Optional: Set PYTHONPATH if your simulation code uses relative imports across modules
# ENV PYTHONPATH=/app

# Run app.py when the container launches
CMD ["python", "app.py"]
