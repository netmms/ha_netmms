ARG BUILD_FROM
FROM ${BUILD_FROM}

# Add bashio & tz, and install snapcast (snapserver)
# Home Assistant base images are Alpine-based
RUN apk add --no-cache \
      bash \
      tzdata \
      curl \
      jq \
      coreutils \
      snapcast \
    && mkdir -p /etc/services.d/snapserver \
               /etc/cont-init.d \
               /usr/local/bin

RUN apk add --no-cache snapcast  # already included

# Copy rootfs (s6, config generator, default config)
COPY rootfs/ /

# Environment
ENV LANG=C.UTF-8

# s6-overlay v3 is already in HA base; just ensure scripts are executable
RUN chmod +x /etc/cont-init.d/00-config \
             /etc/services.d/snapserver/run \
             /etc/services.d/snapserver/finish \
             /usr/local/bin/gen-snapserver-conf

# Healthcheck: ensure TCP control port answers
#HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
#  CMD nc -z 127.0.0.1 1705 || exit 1

# This is to get rid of the end of file error message
# Replace the old HEALTHCHECK with:
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
  CMD wget -qO- http://127.0.0.1:1780/ >/dev/null 2>&1 || exit 1
