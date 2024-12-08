# pyCrossfade runs on python3.7
#   and only debian buster supports it
FROM debian:buster

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

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
RUN pip3 install numpy==1.19.0   
RUN pip3 install pyrubberband       
RUN pip3 install essentia
RUN pip3 install yodel
RUN pip3 install typer
RUN pip3 install mido
RUN pip3 install scipy==1.6.3
RUN pip3 install madmom --no-dependencies


# Copy the current directory contents into the container at /app
# COPY pycrossfade/ pycrossfade/

# Run pycrossfade/cli.py when the container launches
# ENTRYPOINT ["python", "pycrossfade/cli.py"]


CMD ["sleep", "infinity"]
