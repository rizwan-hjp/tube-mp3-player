use pyoxidizer::prelude::*;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize the Python executable
    let mut exe = pyoxidizer::python_exe()?;

    // Add the application icon from the current directory (icon.ico)
    exe = exe.icon("app_icon.ico")?;

    // Proceed with the regular build process
    exe.build()?;

    Ok(())
}
