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

# HTML assets
RUN mkdir -p /html
COPY html/ /html/

# Copy config.yaml so we can extract the version at build time
COPY config.yaml /build_config.yaml

# Generate /html/version.js from the version field in config.yaml
RUN ADDON_VERSION=$(grep -m1 'version:' /build_config.yaml | awk '{print $2}' | tr -d '"\r\n[:space:]' ) \
    && echo "window.WM_VERSION = \"${ADDON_VERSION}\";" > /html/version.js \
    && rm /build_config.yaml

# Fix permissions
RUN chmod a+x /run.sh /pa.py /play_msg.sh

# Start script
CMD [ "/run.sh" ]
