FROM python:3.12-slim-bookworm

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh


# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh



# Ensure /data directory exists
RUN mkdir -p /data


# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"



# Expose port
EXPOSE 8000


WORKDIR /app
COPY proj01.py /app
COPY datagen.py /data
COPY evaluate.py /data

RUN pip install --no-cache-dir fastapi uvicorn requests
CMD ["uv","run","proj01.py"]
