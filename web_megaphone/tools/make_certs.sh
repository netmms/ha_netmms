#!/bin/bash
# Makes the HTTPS certificate for the Web Megaphone page, signed by a small
# home certificate authority (CA) that your phones and computers trust once.
#
#   bash web_megaphone/tools/make_certs.sh [output folder]     (default: ha_netmms/_certs)
#
# First run: creates the home CA (10 years) and the add-on certificate.
# Later runs: keep the CA, make a new add-on certificate (renew every ~2 years:
# Apple accepts at most 825 days).
#
# The CA may only vouch for the home network (name constraints): 192.168.100.x,
# *.local and "homeassistant". Even if its key leaked it could not fake any
# other site. Still: ca.key.pem never goes to git or to Home Assistant.
#
# Files made:
#   ca.key.pem              the CA key: keep it here, nowhere else
#   ca.crt                  install this on each phone / computer (once)
#   wm.cert.pem, wm.key.pem copy these two to Home Assistant: /ssl/web_megaphone/
set -e

HOST_IP="${HOST_IP:-192.168.100.4}"
NET="${NET:-192.168.100.0/255.255.255.0}"
NAMES="${NAMES:-homeassistant.local homeassistant}"
DAYS_CA=3650
DAYS_CERT=825

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$HERE/../../_certs}"
mkdir -p "$OUT"
cd "$OUT"
umask 077

if [ ! -f ca.key.pem ] || [ ! -f ca.crt ]; then
  echo "=== making the home CA"
  cat > ca.cnf <<EOF
[req]
distinguished_name = dn
prompt = no
x509_extensions = ca_ext
[dn]
CN = Home PA CA (192.168.100.x only)
O = netmms home
[ca_ext]
basicConstraints = critical, CA:TRUE, pathlen:0
keyUsage = critical, keyCertSign, cRLSign
subjectKeyIdentifier = hash
nameConstraints = critical, permitted;IP:${NET}, permitted;DNS:local, permitted;DNS:homeassistant
EOF
  openssl req -x509 -new -newkey rsa:2048 -nodes -sha256 -days $DAYS_CA \
    -keyout ca.key.pem -out ca.crt -config ca.cnf
  rm -f ca.cnf
else
  echo "=== keeping the home CA ($(openssl x509 -in ca.crt -noout -enddate))"
fi

echo "=== making the add-on certificate for ${HOST_IP} ${NAMES}"
SAN="IP:${HOST_IP}"
for n in $NAMES; do SAN="${SAN}, DNS:${n}"; done
cat > wm.cnf <<EOF
[req]
distinguished_name = dn
prompt = no
[dn]
CN = ${HOST_IP}
O = Web Megaphone
[ext]
basicConstraints = critical, CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = ${SAN}
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid
EOF
openssl req -new -newkey rsa:2048 -nodes -sha256 -keyout wm.key.pem -out wm.csr -config wm.cnf
openssl x509 -req -in wm.csr -CA ca.crt -CAkey ca.key.pem -CAcreateserial -sha256 \
  -days $DAYS_CERT -extfile wm.cnf -extensions ext -out wm.cert.pem
rm -f wm.csr wm.cnf ca.srl
chmod 644 ca.crt wm.cert.pem

openssl verify -CAfile ca.crt wm.cert.pem
echo
echo "Done, in $(pwd):"
echo "  copy to Home Assistant /ssl/web_megaphone/ :  wm.cert.pem  wm.key.pem  ca.crt"
echo "  install on each device (once):                ca.crt"
echo "  keep private, never copy anywhere:            ca.key.pem"
openssl x509 -in wm.cert.pem -noout -enddate | sed 's/notAfter=/  certificate valid until: /'
