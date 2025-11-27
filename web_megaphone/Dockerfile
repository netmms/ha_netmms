ARG BUILD_FROM
FROM $BUILD_FROM

# Add env
ENV LANG C.UTF-8

# Setup base, install sox package
RUN apk add --no-cache alsa-plugins-pulse alsa-utils
RUN apk add --no-cache jq sox 
RUN apk add --no-cache python3

# Python 3 HTTP Server serves the current working dir
# So let's set it to our add-on persistent data directory.
# WORKDIR /data

# Copy data
COPY run.sh pa.py play_msg.sh /
COPY pa_sound.wav /
COPY pzpray.local.key.pem pzpray.local.cert.pem /
# Copies only the files, no way otherwisd
RUN mkdir /html
COPY html /html
# COPY run.sh /

RUN chmod a+x /run.sh /play_msg.sh

CMD [ "/run.sh" ]
