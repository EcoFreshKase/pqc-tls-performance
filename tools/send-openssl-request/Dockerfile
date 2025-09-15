ARG CA_CERT_PATH
ARG BACKEND_URL
ARG DEFAULT_GROUPS=mlkem512:mlkem768:mlkem1024:X25519MLKEM768:SecP256r1MLKEM768
ARG LIBOQS_TAG=0.14.0
ARG OQSPROVIDER_TAG=0.10.0

# --- First stage: Build ---
FROM rust:1.89-bookworm AS builder

WORKDIR /app
COPY . .

RUN cargo build --release

# --- Final stage: Final image ---
FROM debian:trixie-slim
ARG CA_CERT_PATH
ARG BACKEND_URL
ARG DEFAULT_GROUPS
ARG LIBOQS_TAG
ARG OQSPROVIDER_TAG

ENV GROUPS=${DEFAULT_GROUPS}
ENV CA_CERT_PATH=${CA_CERT_PATH}
ENV BACKEND_URL=${BACKEND_URL}

COPY --from=builder /app/target/release/quantum-safe-reqwest /usr/local/bin/quantum-safe-reqwest

# # 1. Install openssl
RUN apt-get update && \
    apt-get install -y --no-install-recommends openssl

# 2. Install liboqs
RUN apt install -y astyle cmake gcc ninja-build libssl-dev python3-pytest python3-pytest-xdist \ 
    unzip xsltproc doxygen graphviz python3-yaml valgrind build-essential pkg-config git

WORKDIR /usr/local

RUN git clone --depth 1 --branch ${LIBOQS_TAG} https://github.com/open-quantum-safe/liboqs.git && \
    cd liboqs && \
    mkdir build && \
    cd build && \
    cmake -GNinja .. && \
    ninja && \
    ninja install

# 3. Install oqs-provider
RUN git clone --depth 1 --branch ${OQSPROVIDER_TAG} https://github.com/open-quantum-safe/oqs-provider.git && \
    cd oqs-provider && \
    cmake -S . -B _build && \
    cmake --build _build && \
    cmake --install _build

# Make groups configurable via environment variable
RUN awk -v groups="$GROUPS" 'BEGIN { in_section=0 } \
/^\[openssl_init\]/ { \
    print "[openssl_init]"; \
    print "providers = provider_sect"; \
    print "ssl_conf = ssl_sect"; \
    in_section = 1; \
    next; \
} \
in_section && /^\[/ { \
    in_section = 0; \
    print ""; \
    print "[ssl_sect]"; \
    print "system_default = system_default_sect"; \
    print ""; \
    print "[system_default_sect]"; \
    print "Groups = " groups; \
    print ""; \
    print "[provider_sect]"; \
    print "default = default_sect"; \
    print "oqsprovider = oqsprovider_sect"; \
    print ""; \
    print "[default_sect]"; \
    print "activate = 1"; \
    print ""; \
    print "[oqsprovider_sect]"; \
    print "activate = 1"; \
} \
!in_section || /^\[/ { print }' /etc/ssl/openssl.cnf > /etc/ssl/openssl.cnf.new && \
mv /etc/ssl/openssl.cnf.new /etc/ssl/openssl.cnf
    
ENTRYPOINT ["/usr/local/bin/quantum-safe-reqwest"]
