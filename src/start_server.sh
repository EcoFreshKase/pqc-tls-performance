#!/bin/bash
set -e

if [ "${USE_OSSL35:-0}" = "1" ]; then
    : "Using OpenSSL 3.5 from $HOME/openssl-3.5"
    export PATH="$HOME/openssl-3.5/bin:$PATH"
    export LD_LIBRARY_PATH="$HOME/openssl-3.5/lib:$LD_LIBRARY_PATH"
    >&2 echo "USE_OSSL35 set: prepended $HOME/openssl-3.5 to PATH and LD_LIBRARY_PATH"
fi

openssl s_server -cert $CERT_PATH \
    -key $KEY_PATH \
    -www -accept localhost:4433 \
    -tls1_3 -curves $KEM_ALG
