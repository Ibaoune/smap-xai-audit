import numpy as np

def compute_error(et_model, et_ref):
    return et_model - et_ref

def compute_value_ae(et_opl, et_da, et_ref):
    e_opl = compute_error(et_opl, et_ref)
    e_da = compute_error(et_da, et_ref)
    return np.abs(e_opl) - np.abs(e_da)

def compute_value_se(et_opl, et_da, et_ref):
    e_opl = compute_error(et_opl, et_ref)
    e_da = compute_error(et_da, et_ref)
    return (e_opl ** 2) - (e_da ** 2)

def compute_value_nae(et_opl, et_da, et_ref, epsilon=1e-4):
    e_opl = compute_error(et_opl, et_ref)
    e_da = compute_error(et_da, et_ref)
    num = np.abs(e_opl) - np.abs(e_da)
    den = np.abs(e_opl) + np.abs(e_da) + epsilon
    return num / den

def compute_value_refnorm(et_opl, et_da, et_ref, epsilon_ref=0.05):
    e_opl = compute_error(et_opl, et_ref)
    e_da = compute_error(et_da, et_ref)
    num = np.abs(e_opl) - np.abs(e_da)
    den = np.abs(et_ref) + epsilon_ref
    return num / den

def compute_error_ratio(et_opl, et_da, et_ref, epsilon=1e-4):
    e_opl = compute_error(et_opl, et_ref)
    e_da = compute_error(et_da, et_ref)
    num = np.abs(e_da) + epsilon
    den = np.abs(e_opl) + epsilon
    return num / den

def compute_log_error_ratio(et_opl, et_da, et_ref, epsilon=1e-4):
    ratio = compute_error_ratio(et_opl, et_da, et_ref, epsilon)
    return np.log(ratio)
