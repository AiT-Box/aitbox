mod ffi;

use pyo3::prelude::*;


#[pymodule]
fn map_match(m: &Bound<'_, PyModule>) -> PyResult<()> {
    ffi::bindings::register(m)?;
    Ok(())
}
