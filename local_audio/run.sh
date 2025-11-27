#!/usr/bin/with-contenv bashio

DEF_VOL=$(bashio::config 'volume')
USE_PIPE=$(bashio::config 'use_pipe')
PIPE_PATH=$(bashio::config 'pipe')

# Default pipe path if use_pipe is true but pipe is empty
if bashio::var.has_value "${USE_PIPE}"; then
    if bashio::config.true 'use_pipe'; then
        if [[ -z "${PIPE_PATH}" || "${PIPE_PATH}" == "null" ]]; then
            PIPE_PATH="/share/snapserver/stream"
        fi
        bashio::log.info "Pipe mode enabled. Using pipe: ${PIPE_PATH}"
    else
        bashio::log.info "Pipe mode disabled. Using local ALSA playback."
    fi
else
    # If use_pipe not defined, default to false
    USE_PIPE="false"
    bashio::log.info "use_pipe not set. Defaulting to local ALSA playback."
fi

bashio::log.info "Starting new session..."
bashio::log.info "Default volume = ${DEF_VOL}%"

amixer sset Master ${DEF_VOL}%

# Read from STDIN aliases to play file
while read -r input; do

    echo "======================================================="

    # removing JSON stuff
    input="$(echo "$input" | jq --raw-output '.')"
    bashio::log.info "Read alias: ${input}"

    IFS=';' read -r -a arg <<< "$input"
    # remove leading/trailing spaces
    file=$(echo "${arg[0]}" | xargs)

    # is volume present?
    if (( ${#arg[@]} < 2 )); then
        vol="def"
    else
        vol=$(echo "${arg[1]}" | xargs)
    fi

    # "${vol,,}" = convert to lower case
    if [[ -z "${vol}" || "${vol,,}" == "def" ]]; then
        vol=${DEF_VOL}
        bashio::log.info ">> Using default volume (${vol}%)..."
    fi

    bashio::log.info ">> Setting volume to ${vol}%..."
    amixer sset Master "${vol}%" >/dev/null 2>&1

    if [[ ${file: -1} == "/" ]]; then
        bashio::log.warning ">> No file specified, skipping..."
    else
        bashio::log.info ">> Playing media ${file}..."

        if bashio::config.true 'use_pipe'; then
            # Pipe mode: send raw PCM to named pipe (for Snapserver Pipe)
            bashio::log.info ">> Output via pipe: ${PIPE_PATH}"
            if ! msg="$(sox "${file}" -t raw -b 16 -e signed -r 48000 -c 2 "${PIPE_PATH}" 2>&1)"; then
                bashio::log.error "Playing via pipe failed -> ${msg}"
            fi
        else
            # Local ALSA playback
            bashio::log.info ">> Output via local ALSA"
            if ! msg="$(play -q "${file}" --buffer 32768 -t alsa 2>&1)"; then
                bashio::log.error "Playing via ALSA failed -> ${msg}"
            fi
        fi
    fi
done
