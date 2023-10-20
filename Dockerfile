# Use an official Python runtime as a parent image
FROM python:3.11-bullseye

# Set the working directory to /app
WORKDIR /app

RUN apt update -y && apt install -y libsndfile1 rubberband-cli ffmpeg
# Install any needed packages specified in requirements.txt
# COPY requirements.txt .
RUN pip install Cython 
RUN pip install numpy  
RUN pip install pyrubberband  
RUN pip install madmom  
RUN pip install essentia
RUN pip install yodel
RUN pip install   


# Copy the current directory contents into the container at /app
COPY pycrossfade/ .

# Define environment variable
ENV NAME PyCrossfade

# Run app.py when the container launches
CMD ["python", "cli.py"]
