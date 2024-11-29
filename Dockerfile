# Use an official Python runtime as a parent image
FROM python:3.8

WORKDIR /app

RUN apt update -y && apt install -y libsndfile1 rubberband-cli ffmpeg
RUN pip install Cython 
RUN pip install numpy  
RUN pip install pyrubberband  
RUN pip install madmom  
RUN pip install essentia
RUN pip install yodel
# RUN pip install   


# Copy the current directory contents into the container at /app
COPY pycrossfade/ .

# Define environment variable
ENV NAME=pyCrossfade

# Run app.py when the container launches
CMD ["python", "cli.py"]
