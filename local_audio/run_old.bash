#!/usr/bin/env bashio

DEF_VOL=$(bashio::config 'volume')

bashio::log.info "Starting new session..."
bashio::log.info "Default volume = ${DEF_VOL}"

amixer sset Master ${DEF_VOL}%

# Read from STDIN aliases to play file

while read -r input; do

	echo "======================================================="

    # removing JSON stuff
    input="$(echo "$input" | jq --raw-output '.')"
	bashio::log.info "Read alias: ${input}"

	IFS=';' read -r -a arg <<< "$input"
	# remove leading/trailing spaces
	file=$(echo ${arg[0]} | xargs)

	# is volume present?
	if (( ${#arg[@]} < 2 )); then
		# vol=""
		# vol=${DEF_VOL}
		vol="DEF"
	else
		vol=$(echo ${arg[1]} | xargs)
	fi


	if [ -n "$vol" ]; then

	if (( ${#arg[@]} >= 2 )); then
		vol=$(echo ${arg[1]} | xargs)
		# vol=""
		vol=${DEF_VOL}
	else
	fi

	bashio::log.info "File=${file}"
	bashio::log.info "Volume=${vol}"

	# set volume?
	if [ -n "$vol" ]; then
		bashio::log.info ">> Setting volume to ${vol}%..."
		amixer sset Master $vol%
	else
		# bashio::log.info ">> Using default volume..."
		bashio::log.info ">> Not setting volume..."
	fi

	# file="/config/www/$file"
	# file="http://127.0.0.1:8123/local/$file"
	# echo "file=$file"

	if [ -z $file ]; then
		bashio::log.warning ">> No file specified, skipping..."
	else
		bashio::log.info ">> Playing media file..."
		if ! msg="$(play -q $file -t alsa)"; then
			bashio::log.error "Playing failed -> ${msg}"
		fi
    fi
done
