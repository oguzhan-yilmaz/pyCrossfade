# Use an official Python runtime as a parent image
FROM python:3.8-bookworm

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt update -y \
    && apt install -y libsndfile1 rubberband-cli ffmpeg \
    && apt autoremove -y 


# i know this is ugly but its the only configuration that works
RUN pip install Cython \
    && pip install numpy==1.19.0 pyrubberband essentia yodel typer scipy mido \ 
    && pip install madmom --no-dependencies


# Copy the current directory contents into the container at /app
# COPY pycrossfade/ pycrossfade/

# Define environment variable
ENV NAME=pyCrossfade

# Run app.py when the container launches
# CMD ["python", "pycrossfade/cli.py"]
CMD ["sleep", "infinity"]
