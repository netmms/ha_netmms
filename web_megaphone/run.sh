#!/usr/bin/with-contenv bashio

DEF_VOL1=$(bashio::config 'volume1')
DEF_VOL2=$(bashio::config 'volume2')

bashio::log.info "Starting new session..."
bashio::log.info "Volume #1 = ${DEF_VOL1}"
bashio::log.info "Volume #2 = ${DEF_VOL2}"
# amixer sset Master ${DEF_VOL}%

bashio::log.info "Starting HTTP server..."
bashio::log.info "$(python3 -V)"
python3 pa.py
