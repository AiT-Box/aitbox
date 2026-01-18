use pyo3::prelude::*;
use numpy::{PyArray2, PyReadonlyArray2};


#[pyfunction]
pub fn map_match(
    road_network: PyReadonlyArray2<PyObject>,
    trajectories: Vec<PyReadonlyArray2<f64>>,
) -> PyResult<Vec<Py<PyArray2<PyObject>>>> {
    println!("Rust map_match 调试：函数已成功触发！");
    Ok(vec![])
}


pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(map_match, m)?)?;
    Ok(())
}
