use std::env;
use std::fs::File;
use std::io::Read;
use reqwest::Certificate;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let ca_path = env::var("CA_CERT_PATH").unwrap();
    let backend_url = env::var("BACKEND_URL").unwrap();

    if ca_path.is_empty() || backend_url.is_empty() {
        eprintln!("Environment variables CA_CERT_PATH and BACKEND_URL must be set. CA_CERT_PATH='{}', BACKEND_URL='{}'", ca_path, backend_url);
        std::process::exit(1);
    }

    let mut root_certificate_buf = Vec::new();

    match File::open(ca_path) {
        Ok(mut file) => {
            file.read_to_end(&mut root_certificate_buf)?;
        }
        Err(e) => {
            eprintln!("Failed to open CA certificate: {}", e);
            return Err(e.into());
        }
    }

    let cert = Certificate::from_pem(&root_certificate_buf)?;
    
    let client = reqwest::blocking::Client::builder()
        .add_root_certificate(cert)
        .use_native_tls()
        .build()?;
    
    let res = client.get(format!("{}/testfile.txt", backend_url))
        .send()
        .inspect_err(|e| eprintln!("Request failed: {}", e));

    if let Ok(resp) = res {
        match resp.text() {
            Ok(text) => println!("Response: {}", text),
            Err(e) => eprintln!("Failed to read response text: {}", e),
        }
    }


    Ok(())
}
