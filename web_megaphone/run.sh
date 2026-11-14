#!/usr/bin/with-contenv bashio

DEF_VOL1=$(bashio::config 'volume1')
DEF_VOL2=$(bashio::config 'volume2')

bashio::log.info "Starting new session..."
bashio::log.info "Volume #1 = ${DEF_VOL1}"
bashio::log.info "Volume #2 = ${DEF_VOL2}"
# amixer sset Master ${DEF_VOL}%

# HTTPS certificate: the trusted one in /ssl/web_megaphone (see README,
# "Certificates"). Without it, make a throwaway self-signed one in /data
# (browsers warn), so the page still works.
if [[ ! -s /ssl/web_megaphone/wm.cert.pem || ! -s /ssl/web_megaphone/wm.key.pem ]]; then
    if ! openssl x509 -in /data/wm.cert.pem -noout -checkend 86400 >/dev/null 2>&1 \
       || [[ ! -s /data/wm.key.pem ]]; then
        bashio::log.info "No certificate in /ssl/web_megaphone: making a self-signed one"
        openssl req -x509 -newkey rsa:2048 -nodes -sha256 -days 825 \
            -keyout /data/wm.key.pem -out /data/wm.cert.pem \
            -subj "/CN=homeassistant.local" \
            -addext "subjectAltName=DNS:homeassistant.local,DNS:homeassistant" >/dev/null 2>&1 \
            || bashio::log.error "Could not make a certificate"
        chmod 600 /data/wm.key.pem 2>/dev/null
    fi
fi

bashio::log.info "Starting HTTP server..."
bashio::log.info "$(python3 -V)"
python3 pa.py
