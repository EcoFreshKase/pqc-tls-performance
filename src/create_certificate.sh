#!/bin/bash
set -e

# export CA_KEY_PATH=./tmp/ca.key
# export CA_CERT_PATH=./tmp/ca.crt
# export CERT_PRIV_KEY_PATH=./tmp/server.key
# export CERT_REQUEST_PATH=./tmp/server.csr
# export CERT_PATH=./tmp/server.crt
# export SIG_ALG=mldsa44
# export USE_OSSL35=1

if [ "${USE_OSSL35:-0}" = "1" ]; then
    : "Using OpenSSL 3.5 from $HOME/openssl-3.5"
    export PATH="$HOME/openssl-3.5/bin:$PATH"
    export LD_LIBRARY_PATH="$HOME/openssl-3.5/lib:$LD_LIBRARY_PATH"
    >&2 echo "USE_OSSL35 set: prepended $HOME/openssl-3.5 to PATH and LD_LIBRARY_PATH"
fi

# Create CA
openssl req -x509 -new -newkey $SIG_ALG \
    -keyout $CA_KEY_PATH \
    -out $CA_CERT_PATH -noenc \
    -subj "/CN=pqc-tls-performance-CA" -days 365

# Create certificate request
openssl req -new -newkey $SIG_ALG \
    -keyout $CERT_PRIV_KEY_PATH \
    -out $CERT_REQUEST_PATH -noenc \
    -subj "/CN=localhost"

# Sign certificate request with CA
openssl x509 -req -in $CERT_REQUEST_PATH \
    -out $CERT_PATH -CA $CA_CERT_PATH \
    -CAkey $CA_KEY_PATH -CAcreateserial \
    -days 365 -extfile cert.cnf \
    -extensions v3_req
