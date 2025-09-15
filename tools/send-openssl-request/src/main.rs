use std::env;
use std::fs::File;
use std::io::Read;
use std::time::Duration;
use reqwest::Certificate;
use tokio::time::sleep;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let ca_path = env::var("CA_CERT_PATH").unwrap();
    let backend_url = env::var("BACKEND_URL").unwrap();

    if ca_path.is_empty() || backend_url.is_empty() {
        eprintln!("Environment variables CA_CERT_PATH and BACKEND_URL must be set. CA_CERT_PATH='{}', BACKEND_URL='{}'", ca_path, backend_url);
        std::process::exit(1);
    }

    println!("Using CA certificate from: {}", ca_path);
    println!("Sending requests to backend URL: {}", backend_url);

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
    
    let client = reqwest::Client::builder()
        .add_root_certificate(cert)
        .use_native_tls()
        .build()?;
    
    let max_requests = 10000;
    let mut counter = 0;
    while counter < max_requests {
        println!("Sending request #{} to {}...", counter, backend_url);
        let res = client.get(format!("{}/testfile.txt", backend_url))
            .send()
            .await.inspect_err(|e| eprintln!("Request failed: {}", e));

        if let Ok(resp) = res {
            match resp.text().await {
                Ok(text) => println!("Response: {}", text),
                Err(e) => eprintln!("Failed to read response text: {}", e),
            }
        }


        counter += 1; 
        sleep(Duration::from_secs(10)).await;
    }


    println!("Terminated: exceeded {} requests", max_requests);

    Ok(())
}
