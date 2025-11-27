#!/usr/bin/with-contenv bashio

DEF_VOL1=$(bashio::config 'volume1')
DEF_VOL2=$(bashio::config 'volume2')

USE_PIPE=$(bashio::config 'use_pipe')
PIPE_PATH=$(bashio::config 'pipe')

bashio::log.info "Playing message: vol1=${DEF_VOL1} vol2=${DEF_VOL2} pipe=${USE_PIPE}"

if [[ "${USE_PIPE}" == "true" ]]; then
    bashio::log.info "Output = PIPE -> ${PIPE_PATH}"

    # Safety: ensure the pipe exists
    if [[ ! -p "${PIPE_PATH}" ]]; then
        bashio::log.error "PIPE missing: ${PIPE_PATH}"
        exit 1
    fi

    # First tone (pa_sound.wav)
    amixer -q sset Master "${DEF_VOL1}%" >/dev/null 2>&1
    if ! sox pa_sound.wav -t raw -b 16 -e signed -r 48000 -c 2 "${PIPE_PATH}" 2>/dev/null; then
        bashio::log.error "Failed to send pa_sound.wav to pipe."
    fi

    # Message (msg.wav)
    amixer -q sset Master "${DEF_VOL2}%" >/dev/null 2>&1
    if ! sox msg.wav -t raw -b 16 -e signed -r 48000 -c 2 "${PIPE_PATH}" 2>/dev/null; then
        bashio::log.error "Failed to send msg.wav to pipe."
    fi

else
    bashio::log.info "Output = LOCAL ALSA"

    # First tone (pa_sound.wav)
    amixer -q sset Master "${DEF_VOL1}%" >/dev/null 2>&1
    aplay -q pa_sound.wav

    # Message (msg.wav)
    amixer -q sset Master "${DEF_VOL2}%" >/dev/null 2>&1
    aplay -q msg.wav
fi
