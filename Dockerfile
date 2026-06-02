FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application into a subdirectory named 'vg'
COPY . vg/

# Hugging Face Spaces expect apps to run on port 7860
ENV PORT=7860
EXPOSE 7860

# Run the VG web server from the parent directory /app
CMD ["python", "-m", "vg.main", "--web", "--host", "0.0.0.0", "--port", "7860"]
