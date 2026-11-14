#!/usr/bin/with-contenv bashio

# MQTT broker from the Supervisor (the Mosquitto add-on); the add-on options can override it
if bashio::services.available "mqtt"; then
    export MQTT_HOST="$(bashio::services mqtt 'host')"
    export MQTT_PORT="$(bashio::services mqtt 'port')"
    export MQTT_USER="$(bashio::services mqtt 'username')"
    export MQTT_PASSWORD="$(bashio::services mqtt 'password')"
    bashio::log.info "MQTT service found at ${MQTT_HOST}:${MQTT_PORT}"
else
    bashio::log.warning "No MQTT service from the Supervisor; using the mqtt_* options"
fi

cd /app
exec python3 -u prayer_times.py
