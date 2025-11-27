#!/usr/bin/env bashio

DEF_VOL=$(bashio::config 'volume')

bashio::log.info "Starting new session..."
bashio::log.info "Default volume = ${DEF_VOL}"

# amixer sset Master ${DEF_VOL}%

# Read from STDIN aliases to play file

while read -r input; do

	echo "======================================================="

  # removing JSON stuff
  # input="$(echo "$input" | jq --raw-output '.')"
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

  echo "${vol,,}"
	if [[  -z "$vol" || "${vol,,}" == "def" ]]; then
		vol=${DEF_VOL}
		bashio::log.info ">> Using default volume (${vol}%)..."
	fi

	# bashio::log.info "Volume=${vol}"

	bashio::log.info ">> Setting volume to ${vol}%..."
	# amixer sset Master $vol%

	# file="/config/www/$file"
	file_loc="http://127.0.0.1:8123/local/"

	# if [[ -z $file ]]; then
	if [[ ${file: -1} == "/" ]]; then
		bashio::log.warning ">> No file specified, skipping..."
	else
		bashio::log.info ">> Playing media file ${file}..."
		if ! msg="1"; then
			bashio::log.error "Playing failed -> ${msg}"
		fi
    fi
done
