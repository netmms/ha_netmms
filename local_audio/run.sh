#!/usr/bin/with-contenv bashio

DEF_VOL=$(bashio::config 'volume')
USE_PIPE=$(bashio::config 'use_pipe')
PIPE_PATH=$(bashio::config 'pipe')
FOLDER=$(bashio::config 'folder')

# Defaults / sanity
if [[ -z "${FOLDER}" || "${FOLDER}" == "null" ]]; then
    FOLDER="/config/www"
fi

if bashio::config.true 'use_pipe'; then
    if [[ -z "${PIPE_PATH}" || "${PIPE_PATH}" == "null" ]]; then
        PIPE_PATH="/share/snapserver/stream"
    fi
    bashio::log.info "Pipe mode enabled. Using pipe: ${PIPE_PATH}"
else
    bashio::log.info "Pipe mode disabled. Using local ALSA playback."
fi

bashio::log.info "Starting new session..."
bashio::log.info "Default volume = ${DEF_VOL}%"
bashio::log.info "Media base folder = ${FOLDER}"

amixer sset Master "${DEF_VOL}%" >/dev/null 2>&1

# Read from STDIN aliases to play file
while read -r input; do

    echo "======================================================="

    # removing JSON stuff
    input="$(echo "$input" | jq --raw-output '.')"
    bashio::log.info "Read alias: ${input}"

    IFS=';' read -r -a arg <<< "$input"
    raw_file=$(echo "${arg[0]}" | xargs)

    # Determine full file path:
    # If raw_file starts with "/", use it as-is.
    # Otherwise, prepend FOLDER.
    if [[ "$raw_file" == /* ]]; then
        file="$raw_file"
    else
        file="${FOLDER}/${raw_file}"
    fi

    bashio::log.info "Resolved file path = ${file}"

    # Volume handling
    if (( ${#arg[@]} < 2 )); then
        vol="def"
    else
        vol=$(echo "${arg[1]}" | xargs)
    fi

    if [[ -z "${vol}" || "${vol,,}" == "def" ]]; then
        vol=${DEF_VOL}
        bashio::log.info ">> Using default volume (${vol}%)..."
    fi

    bashio::log.info ">> Setting volume to ${vol}%..."
    amixer sset Master "${vol}%" >/dev/null 2>&1

    # Basic validation
    if [[ ${file: -1} == "/" ]]; then
        bashio::log.warning ">> No file specified, skipping..."
        continue
    fi

    if [[ ! -f "${file}" ]]; then
        bashio::log.error ">> File not found: ${file}, skipping..."
        continue
    fi

    bashio::log.info ">> Playing media ${file}..."

    if bashio::config.true 'use_pipe'; then
        bashio::log.info ">> Output via pipe: ${PIPE_PATH}"
        if ! msg="$(sox "${file}" -t raw -b 16 -e signed -r 48000 -c 2 "${PIPE_PATH}" 2>&1)"; then
            bashio::log.error "Playing via pipe failed -> ${msg}"
        fi
    else
        bashio::log.info ">> Output via local ALSA"
        if ! msg="$(play -q "${file}" --buffer 32768 -t alsa 2>&1)"; then
            bashio::log.error "Playing via ALSA failed -> ${msg}"
        fi
    fi

done
