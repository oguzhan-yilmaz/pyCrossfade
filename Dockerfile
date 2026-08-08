# pyCrossfade runs on python3.7
#   and only debian buster supports it
# Built/pulled as linux/amd64 (x86_64 wheels exist for all pinned deps).
# This matches the ghcr.io/oguzhan-yilmaz/pycrossfade published image.
FROM --platform=linux/amd64 debian:buster
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app


# move to archive.debian.org package index
RUN sed -i \
      -e 's|deb.debian.org/debian|archive.debian.org/debian|g' \
      -e 's|deb.debian.org/debian-security|archive.debian.org/debian-security|g' \
      /etc/apt/sources.list \
    && printf 'Acquire::Check-Valid-Until "false";\n' \
       > /etc/apt/apt.conf.d/99no-check-valid-until

# install essentia dependencies: https://essentia.upf.edu/installing.html
RUN apt-get update -y \
    && apt-get install -y build-essential libeigen3-dev libyaml-dev libfftw3-dev libavcodec-dev libavformat-dev libavutil-dev libswresample-dev libsamplerate0-dev libtag1-dev libchromaprint-dev \
    && apt-get autoremove -y 

RUN apt-get install -y python3.7-dev
RUN apt-get install -y python3-pip
    
# install pyCrossfade dependencies
RUN apt-get install -y libsndfile1 rubberband-cli ffmpeg \
    && apt-get install -y libffi6 libffi-dev \
    && apt-get autoremove -y 


# i know this is ugly but its the only configuration that works
RUN pip3 install Cython==0.29.36 setuptools==50.1.0

RUN python3 -m pip install numpy==1.19.0

RUN pip3 install pyrubberband==0.4.0

# 0.466 ERROR: Could not find a version that satisfies the requirement essentia==2.1b6.dev374 
# (from versions: 2.1b5.dev416, 2.1b5.dev447, 2.1b5.dev532, 2.1b5.dev707, 2.1b5, 2.1b6.dev90, 2.1b6.dev184, 2.1b6.dev234)
RUN pip3 install essentia==2.1b6.dev374
RUN pip3 install yodel==0.3.0
RUN pip3 install typer==0.14.0
RUN pip3 install mido==1.3.3
RUN pip3 install scipy==1.6.3
RUN pip3 install madmom==0.16.1 --no-dependencies


# Copy the current directory contents into the container at /app
COPY pycrossfade/ pycrossfade/

# Run the pycrossfade CLI package. pycrossfade/ is a proper package (relative
# imports), so it must be launched with -m, not as a bare script.
ENTRYPOINT ["python3", "-m", "pycrossfade.cli"]


# CMD ["sleep", "infinity"]
