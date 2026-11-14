# The Supervisor passes only BUILD_ARCH and BUILD_VERSION, so BUILD_FROM needs a default
ARG BUILD_ARCH=amd64
ARG BUILD_FROM=ghcr.io/home-assistant/${BUILD_ARCH}-base:latest
FROM ${BUILD_FROM}

ENV LANG C.UTF-8

# python, the MQTT client, and the time zone database
RUN apk add --no-cache python3 py3-paho-mqtt tzdata

# Copy data
COPY prayer_calc.py prayer_times.py /app/
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
