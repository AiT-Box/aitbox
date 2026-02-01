//! -*- coding: utf-8 -*-
//!
//! File        :
//! Project     : rust
//! Author      : gdd
//! Created     : 2026/1/18
//! Description :

#![allow(dead_code)]

mod ffi;
mod geometry;
mod matching;
mod schemas;

use pyo3::prelude::*;

 
#[pymodule]
fn map_match(m: &Bound<'_, PyModule>) -> PyResult<()> {
    ffi::bindings::register(m)?;
    Ok(())
}
