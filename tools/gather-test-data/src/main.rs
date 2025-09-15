use std::process::{Command, Output};

fn main() -> Result<(), Box<dyn std::error::Error>> {


    let output: Output = Command::new("perf")
        .arg("stat")
        .arg("-e")
        .arg("cycles")
        .arg(get_binary_paths()[0])
        .output()?;
    
    
    println!("\x1b[32mStandard Output:\x1b[0m\n{}", String::from_utf8_lossy(&output.stdout));
    println!("\x1b[31mStandard Error:\x1b[0m\n{}", String::from_utf8_lossy(&output.stderr));

    if output.status.success() {
        println!("\x1b[32mCommand executed successfully!\x1b[0m");
    } else {
        println!("\x1b[31mCommand failed with status: {}\x1b[0m", output.status);
    }

    Ok(())
}

fn get_binary_paths() -> Vec<&'static str> {
    if cfg!(debug_assertions) {
        vec!["target/debug/send-openssl-request"]
    } else {
        vec!["target/release/send-openssl-request"]
    }
}
