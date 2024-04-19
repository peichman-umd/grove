# Pull base image
FROM python:3.11.4-slim

# Install git
RUN apt-get update && \
    apt-get install -y git xmlsec1 && \
    apt-get clean

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /opt/grove

# Install dependencies
COPY pyproject.toml .
RUN pip install -e .[prod]

# Copy project
COPY src ./src
COPY attribute-maps ./attribute-maps
RUN pip install -e .[prod]
RUN src/manage.py collectstatic

# PORT
EXPOSE 5000

# Commands to run migration and start the server
CMD sh -c "src/manage.py migrate && grove"
