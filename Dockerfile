FROM python:3.13

# Set working directory
WORKDIR /app

# Copy project files
COPY proj01.py /app/proj01.py
COPY requirements.txt /app/requirements.txt

# Ensure /data directory exists
RUN mkdir -p /data

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Command to run the FastAPI server
CMD ["uv", "proj01:app", "--host", "0.0.0.0", "--port", "8000"]
