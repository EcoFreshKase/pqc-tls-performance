# Prerequisites
- OpenSSL 3.0.0
- ops-provider 0.10.1
- Both the default provider and the oqsprovider need to be active
  - see the [oqs-provide README](https://github.com/open-quantum-safe/oqs-provider) on how to install the oqsprovider
- pqsprovider 0.2.0

# Installation

Create a side installation of openssl3.5
```bash
wget https://www.openssl.org/source/openssl-3.5.1.tar.gz
tar xvf openssl-3.5.1.tar.gz
cd openssl-3.5.1
./Configure --prefix=$HOME/openssl-3.5 --libdir=lib
make -j$(nproc)
make install_sw
```

# Vorgehensweise

- Wie genau und welche Werte will ich aufnehmen?
    - Welche Algorithmen?
      - Sowohl PQC als auch klassisch
        - Klassisch: RSA, ECC ?
        - PQC: ?
    - Durchsatz -> wie schnell können Verbindungen aufgebaut werden? $\to$ Anzahl aufgebauter Verbindungen pro Zeiteinheit
    - Rechenaufwand -> CPU Cycles eine request zu senden
    - `taskset` to pin process to one cpu
    - `perf` to meassure the cycles
    - `cset` (installiertm it `cpuset`) nutzen um einen Kern zu isolieren
- Wie vergleiche ich die Werte

# Algorithmen

Für FIPS Algorithmen: http://nist.gov/news-events/news/2024/08/nist-releases-first-3-finalized-post-quantum-encryption-standards

liboqs nutzen $\to$ neuere Version und zum Vergleichen

- [Unterstützt](https://github.com/aws/aws-lc/blob/main/crypto/fipsmodule/PQREADME.md) - ML-KEM - ML-DSA
  openssl 3.5
- [Unterstützt](https://openssl-library.org/post/2025-04-08-openssl-35-final-release/) - ML-KEM - ML-DSA - SLH-DSA
  weitere Implementierungen?
- pqsiehld supported ML-KEM und ML-DSA

Mehr Algorithmen als die FIPS 203, 204, 205? Sind andere PQC noch interessant?

## Key-Exchange-Algorithmen

- ML-KEM (CRYSTALS-Kyber) (FIPS 203)
  - ML-KEM-512
    - NIST Level 1
  - ML-KEM-768
    - NIST Level 3
  - ML-KEM-1024
    - NIST Level 5
- RSA
  - RSA-3072
    - NIST Level 1
  - RSA-7680
    - NIST Level 3
  - RSA-15360
    - NIST Level 5
- ECC
  - P-256
    - NIST Level 1
  - P-384
    - NIST Level 3
  - P-521
    - NIST Level 5

## Signier-Algorithmen

- ML-DSA (CRYSTALS-Dilithium) (FIPS 204)
  - ML-DSA-44
    - NIST Level 2
  - ML-DSA-65
    - NIST Level 3
  - ML-DSA-87
    - NIST Level 5
- SLH-DSA (Sphincs+) (FIPS 205)
  - SPHINCS+-SHAKE-128f-simple
    - NIST Level 1
  - SPHINCS+-SHAKE-192f-simple
    - NIST Level 3
  - SPHINCS+-SHAKE-256f-simple
    - NIST Level 5
- RSA
- ECC
