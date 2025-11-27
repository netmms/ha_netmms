# Set base image from Home Assistant build system
ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

# Environment settings
ENV LANG=C.UTF-8

# Install dependencies
RUN apk add --no-cache \
    alsa-plugins-pulse \
    alsa-utils \
    jq \
    sox \
    python3

# Copy scripts and assets
COPY run.sh pa.py play_msg.sh /
COPY pa_sound.wav /
COPY wm.cert.pem wm.key.pem /certs/

# Copies only the files, no way otherwise
RUN mkdir /html
COPY html /html

# Fix permissions
RUN chmod a+x /run.sh /pa.py /play_msg.sh

# Start script
CMD [ "/run.sh" ]
