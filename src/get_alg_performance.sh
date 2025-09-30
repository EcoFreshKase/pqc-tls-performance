#!/bin/bash
set -e

# export TEST_TIME=1
# export USE_OSSL35="1"
# export ALG=MLKEM512

if [ "${USE_OSSL35:-0}" = "1" ]; then
    : "Using OpenSSL 3.5 from $HOME/openssl-3.5"
    export PATH="$HOME/openssl-3.5/bin:$PATH"
    export LD_LIBRARY_PATH="$HOME/openssl-3.5/lib:$LD_LIBRARY_PATH"
    >&2 echo "USE_OSSL35 set: prepended $HOME/openssl-3.5 to PATH and LD_LIBRARY_PATH"
fi

openssl speed -seconds $TEST_TIME $ALG
