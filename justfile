# pyCrossfade — ops via Docker
# Everything runs inside the container (python 3.7 / debian:buster stack).
# The live `pycrossfade/` source is mounted in, so edits are tested WITHOUT
# rebuilding the image — `just build` only needs to happen once (or after
# Dockerfile / dependency changes).

# Image tag for local dev
IMAGE := "pycrossfade:dev"
# Local dirs (both gitignored) mapped into the container
AUDIO_DIR := env("PYCROSSFADE_AUDIO_DIR", "audios")
ANNOTATIONS_DIR := env("PYCROSSFADE_ANNOTATIONS_DIR", "pycrossfade_annotations")

# shared mount + env flags for container recipes
MOUNTS := "-v '{{ justfile_directory() }}/pycrossfade:/app/pycrossfade' -v '{{ justfile_directory() }}/{{ AUDIO_DIR }}:/app/audios' -v '{{ justfile_directory() }}/{{ ANNOTATIONS_DIR }}:/app/pycrossfade_annotations' -e ANNOTATIONS_DIRECTORY=/app/pycrossfade_annotations -e BASE_AUDIO_DIRECTORY=/app/audios/"

# Show available recipes
default:
    @just --list --justfile {{ justfile() }}

# Build (or rebuild) the dev image from the Dockerfile
build:
    mkdir -p {{ AUDIO_DIR }} {{ ANNOTATIONS_DIR }}
    docker build -t {{ IMAGE }} .

# Run the CLI interactively: `just run crossfade a.mp3 b.mp3 -c 8 -t 8 -o mix.wav`
run *args:
    mkdir -p {{ AUDIO_DIR }} {{ ANNOTATIONS_DIR }}
    docker run --rm -it {{ MOUNTS }} {{ IMAGE }} {{ args }}

# Open a bash shell in the container (debugging)
shell:
    mkdir -p {{ AUDIO_DIR }} {{ ANNOTATIONS_DIR }}
    docker run --rm -it {{ MOUNTS }} --entrypoint /bin/bash -i {{ IMAGE }}

# Import check: does `import pycrossfade` work inside the container?
check-import:
    mkdir -p {{ AUDIO_DIR }} {{ ANNOTATIONS_DIR }}
    docker run --rm {{ MOUNTS }} --entrypoint python3 {{ IMAGE }} -c "import pycrossfade; print('pycrossfade', pycrossfade.__version__, 'OK')"

# Compile-check all package files (fast syntax gate)
check:
    docker run --rm -v '{{ justfile_directory() }}/pycrossfade:/app/pycrossfade' --entrypoint python3 {{ IMAGE }} -m py_compile pycrossfade/__init__.py pycrossfade/cli.py pycrossfade/song.py pycrossfade/utils.py pycrossfade/transition.py && echo "compile OK"

# Run pytest inside the container (installs pytest if missing)
test:
    docker run --rm -v '{{ justfile_directory() }}/pycrossfade:/app/pycrossfade' --entrypoint python3 -m pip install -q pytest {{ IMAGE }}
    docker run --rm -v '{{ justfile_directory() }}/pycrossfade:/app/pycrossfade' --entrypoint python3 {{ IMAGE }} -m pytest -v

# Show CLI help: `just help crossfade` for a subcommand's help
help *args:
    mkdir -p {{ AUDIO_DIR }} {{ ANNOTATIONS_DIR }}
    docker run --rm -it {{ MOUNTS }} {{ IMAGE }} --help {{ args }}

# Remove the dev image
clean:
    docker image rm {{ IMAGE }}
