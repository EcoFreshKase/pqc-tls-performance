import os
import re
import signal
import subprocess
import sys
import logging
import tempfile

from time import sleep
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Tuple


NIST_LEVELS = [1, 3, 5]

TEST_TIME = 1

KEM_ALGS = {
    1: ["mlkem512", "X25519", "P-256"], 
    3: ["mlkem768", "X448", "P-384"], 
    5: ["mlkem1024", "P-521"]
}
SIG_ALGS = {
    1: ["mldsa44", "rsa:3072", "ed25519"],
    3: ["mldsa65", "rsa:7680", "ed448"],
    5: ["mldsa87", "rsa:15360"]
}

MEASUREMENT_FILTERING_REGEX = r"\d+\.\d+\s"
RESULT_FILE = Path("./results/results.csv")

logging.basicConfig(level=logging.DEBUG)

def create_command_with_env(command: str, env: dict[str, str]) -> str:
    return f"export {" export ".join([f"{key}={value} &&" for key, value in env.items()])} {command}"

def create_certificate(sig_alg: str, tmpdir_path: Path, use_openssl_35: bool) -> Tuple[Path, Path]:
    logging.debug(f"Creating certificate with sig_alg: {sig_alg}")
    server_private_key = tmpdir_path / "server.key"
    server_cert = tmpdir_path / "server.crt"

    command_certificate_creation = create_command_with_env(
        "bash ./src/create_certificate.sh",
        {
            "CA_KEY_PATH": str(tmpdir_path / "ca.key"),
            "CA_CERT_PATH": str(tmpdir_path / "ca.crt"),
            "CERT_PRIV_KEY_PATH": str(server_private_key),
            "CERT_REQUEST_PATH": str(tmpdir_path / "server.csr"),
            "CERT_PATH": str(server_cert),
            "SIG_ALG": sig_alg,
            "USE_OSSL35": int(use_openssl_35)
        }
    )


    # Run the certificate creation command, suppress output unless DEBUG
    logging.debug(f"Certificate creation command: {command_certificate_creation}")
    debug = logging.getLogger().isEnabledFor(logging.DEBUG)
    result = subprocess.run(
        command_certificate_creation,
        shell=True,
        capture_output=True,
        text=True
    )
    if debug:
        logging.debug(f"Certificate creation stdout:\n{result.stdout}")
        logging.debug(f"Certificate creation stderr:\n{result.stderr}")
    elif result.returncode != 0:
        logging.error(f"Certificate creation failed: {result.stderr}")

    return server_private_key, server_cert

@contextmanager
def start_server(kem_alg: str, sig_alg: str, use_openssl_35: bool) -> Generator[subprocess.Popen]:
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir_path = Path(tmpdirname)

        key_path, cert_path = create_certificate(sig_alg, tmpdir_path, use_openssl_35)

        command_start_server = create_command_with_env(
            "bash ./src/start_server.sh",
            {
                "KEM_ALG": kem_alg,
                "CERT_PATH": str(cert_path.absolute()),
                "KEY_PATH": str(key_path.absolute()),
                "USE_OSSL35": int(use_openssl_35)
            }
        )

        logging.debug(f"Starting server with (kem_alg | sig_alg): ({kem_alg} | {sig_alg})")
        logging.debug(f"Server command: {command_start_server}")
        process = subprocess.Popen(
            command_start_server,
            shell=True,
            start_new_session=True,
            stdout=subprocess.PIPE if logging.getLogger().isEnabledFor(logging.DEBUG) else subprocess.DEVNULL,
            stderr=subprocess.PIPE if logging.getLogger().isEnabledFor(logging.DEBUG) else subprocess.DEVNULL
        )

        sleep(1)  # Give the server a moment to start

        try:
            yield process
        finally:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                if process.stdout:
                    out = process.stdout.read().decode(errors='replace')
                    if out:
                        logging.debug(f"Server stdout:\n{out}")
                if process.stderr:
                    err = process.stderr.read().decode(errors='replace')
                    if err:
                        logging.warning(f"Server stderr:\n{err}")
            process.wait()
            logging.info("Server process terminated.")

def get_measurement_data(use_openssl_35: bool) -> str:
    command_test = create_command_with_env(
        "bash ./src/test.sh", 
        {
            "TEST_TIME": str(TEST_TIME),
            "USE_OSSL35": int(use_openssl_35)
        }
    )
    logging.info(f"Running performance test")
    logging.debug(f"Test command: {command_test}")
    measurement_stream = os.popen(command_test)
    measurement_output = measurement_stream.read()

    return re.search(MEASUREMENT_FILTERING_REGEX, measurement_output).group()

if __name__ == "__main__":

    ossl35_running = True if len(sys.argv) > 1 and sys.argv[1] == "ossl35" else False
    
    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if RESULT_FILE.exists(follow_symlinks=True):
        logging.error(f"Result file {RESULT_FILE} already exists. Please move or delete it before running the tests.")
        exit(1)

    with open(RESULT_FILE, "w") as result_file:
        result_file.write("nist_level,test_time,KEM,SIG,connections/s\n")
    
    for level in NIST_LEVELS:
        for kem_alg in KEM_ALGS[level]:
            for sig_alg in SIG_ALGS[level]:
                logging.info(f"Testing (KEM | SIG): ({kem_alg} | {sig_alg})")

                with start_server(kem_alg, sig_alg, ossl35_running) as server_process:
                    data = get_measurement_data(ossl35_running)
                    logging.info(f"  Result: {data} connections/s")

                    with open(RESULT_FILE, "a") as result_file:
                        result_file.write(f"{level},{TEST_TIME},{kem_alg},{sig_alg},{data}\n")
    
    logging.info(f"All tests completed. Results saved to {RESULT_FILE}")
