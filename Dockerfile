# Use an official Python runtime as a parent image
FROM debian:bookworm

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# install essentia dependencies: https://essentia.upf.edu/installing.html
RUN apt-get update -y \
    && apt-get install -y build-essential libeigen3-dev libyaml-dev libfftw3-dev libavcodec-dev libavformat-dev libavutil-dev libswresample-dev libsamplerate0-dev libtag1-dev libchromaprint-dev \
    && apt-get autoremove -y 


# install pyCrossfade dependencies
RUN apt-get install -y libsndfile1 rubberband-cli ffmpeg \
    && apt-get autoremove -y 


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
