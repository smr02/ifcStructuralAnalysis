
# Use an official Ubuntu runtime as a parent image
FROM --platform=linux ubuntu:latest

# Set the working directory to /app
WORKDIR /app

# Install Python and Flask dependencies
RUN apt-get update && \
    # apt-get install apt-utils -y && \
    apt-get install -y python3-pip python3-dev && \
    pip3 install Flask 

RUN pip install numpy

RUN pip3 install ifcopenshell

# Copy the current directory contents into the container at /app
COPY . /app


# Set the environment variable for Flask
ENV FLASK_APP=app.py
ENV FLASK_ENVIRONMENT=development
ENV FLASK_DEBUG=1

# Expose port 5000 for Flask
EXPOSE 5000

# Start the Flask application
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]