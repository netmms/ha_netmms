#!/usr/bin/with-contenv bashio
# Plays the PA chime, then a recorded message, through Snapcast (pipe) or the local speaker.
#
#   play_msg.sh [message.wav]        (default /msg.wav; pa.py passes its own file)
#
# The message is cleaned and made loud before it plays (VOICE_FX below):
#   cut the last 0.15 s (the tap on "Send"), cut rumble below 90 Hz, level it,
#   compress it so quiet words come up, peak at -1 dB, then add voice_boost dB
#   with a limiter. With the default 6 a recording comes out near -12 LUFS, about as
#   loud as an Adhan file.
#
# Options (add-on Configuration):
#   volume1      chime volume, percent  (pa_sound.wav is very loud: 30 is plenty)
#   volume2      voice volume, percent  (100 = the full level above)
#   voice_boost  extra dB on the voice, 0-10 (default 6; each +2 is clearly louder)
#   use_pipe     true = Snapcast pipe, false = local speaker (ALSA)
# In pipe mode the volumes are applied here by sox. In local mode they set the
# ALSA Master volume as before.

MSG="${1:-/msg.wav}"
CHIME_SRC=/pa_sound.wav
CHIME=/tmp/wm_chime.wav
VOICE=/tmp/wm_voice.wav

VOL1=$(bashio::config 'volume1')
VOL2=$(bashio::config 'volume2')
BOOST=$(bashio::config 'voice_boost')
USE_PIPE=$(bashio::config 'use_pipe')
PIPE_PATH=$(bashio::config 'pipe')

# keep the numbers sane
num() { [[ "$1" =~ ^[0-9]+$ ]] && echo "$1" || echo "$2"; }
VOL1=$(num "$VOL1" 30);  (( VOL1 > 100 )) && VOL1=100
VOL2=$(num "$VOL2" 100); (( VOL2 > 100 )) && VOL2=100
BOOST=$(num "$BOOST" 6); (( BOOST > 10 )) && BOOST=10
# percent -> sox volume factor (30 -> 0.30)
factor() { awk -v p="$1" 'BEGIN { printf "%.2f", p / 100 }'; }

if [[ ! -s "${MSG}" ]]; then
    bashio::log.error "No message file: ${MSG}"
    exit 1
fi

# the tail cut only on messages longer than 1 s
LEN=$(sox --i -D "${MSG}" 2>/dev/null || echo 0)
TRIM=()
awk -v l="${LEN}" 'BEGIN { exit !(l > 1.0) }' && TRIM=(trim 0 -0.15)

VOICE_FX=(highpass 90 gain -n -3
          compand 0.005,0.15 6:-80,-95,-50,-50,-40,-18,-20,-8,0,-3 -3 -90 0.03
          gain -n -1 gain -l "${BOOST}"
          fade 0.01 -0 0.05)

if [[ "${USE_PIPE}" == "true" ]]; then
    V1=$(factor "${VOL1}"); V2=$(factor "${VOL2}")
else
    V1=1; V2=1          # local mode uses amixer below
fi

# 48 kHz stereo 16-bit, the Snapcast format; same for local playback
if ! sox -V1 "${MSG}" -r 48000 -c 2 -b 16 "${VOICE}" "${TRIM[@]}" "${VOICE_FX[@]}" vol "${V2}"; then
    bashio::log.warning "Could not process the message, playing it as recorded"
    sox -V1 -G "${MSG}" -r 48000 -c 2 -b 16 "${VOICE}" vol "${V2}" || exit 1
fi
sox -V1 -G "${CHIME_SRC}" -r 48000 -c 2 -b 16 "${CHIME}" vol "${V1}" || bashio::log.warning "Could not prepare the chime"

bashio::log.info "Playing message (${LEN%.*}s): chime ${VOL1}%, voice ${VOL2}% +${BOOST}dB, pipe=${USE_PIPE}"

if [[ "${USE_PIPE}" == "true" ]]; then
    if [[ ! -p "${PIPE_PATH}" ]]; then
        bashio::log.error "PIPE missing: ${PIPE_PATH}"
        exit 1
    fi
    # chime and voice in one stream, no gap between them
    PARTS=()
    [[ -s "${CHIME}" ]] && PARTS+=("${CHIME}")
    PARTS+=("${VOICE}")
    if ! sox -V1 -G "${PARTS[@]}" -t raw -b 16 -e signed -r 48000 -c 2 "${PIPE_PATH}"; then
        bashio::log.error "Failed to send the message to the pipe."
        exit 1
    fi
else
    amixer -q sset Master "${VOL1}%" >/dev/null 2>&1
    [[ -s "${CHIME}" ]] && aplay -q "${CHIME}"
    amixer -q sset Master "${VOL2}%" >/dev/null 2>&1
    aplay -q "${VOICE}" || exit 1
fi
exit 0
