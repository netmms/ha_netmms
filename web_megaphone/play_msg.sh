#!/usr/bin/with-contenv bashio

# TMPFILE1=/tmp/adhan.lock
# TMPFILE2=/tmp/pa.lock

# if [ -f $TMPFILE1 ]; then
	# read pid < $TMPFILE1
	# kill -TERM -$pid
	# rm -f $TMPFILE1
# fi

# echo $$ > $TMPFILE2

DEF_VOL1=$(bashio::config 'volume1')
DEF_VOL2=$(bashio::config 'volume2')

bashio::log.info "Playing message at vol1=${DEF_VOL1} vol2=${DEF_VOL2}..."
# bashio::log.info "Volume #1 = ${DEF_VOL1}"
# bashio::log.info "Volume #2 = ${DEF_VOL2}"

#amixer -q sset Master ${DEF_VOL1}% && aplay -q pa_sound.wav && \
#amixer -q sset Master ${DEF_VOL2}% && aplay msg.wav

#amixer -q sset Master ${DEF_VOL1}% && aplay -q pa_sound.wav | cat > /share/snapserver/stream && \
#amixer -q sset Master ${DEF_VOL2}% && aplay msg.wav | cat > /share/snapserver/stream

amixer -q sset Master ${DEF_VOL1}% && sox pa_sound.wav -t raw -b 16 -e signed -r 48000 -c 2 /share/snapserver/stream && \
amixer -q sset Master ${DEF_VOL2}% && sox msg.wav -t raw -b 16 -e signed -r 48000 -c 2 /share/snapserver/stream

# rm -f $TMPFILE2
