import numpy as np

def compute_value_ae(et_opl, et_da, et_ref):
    """
    Computes the absolute-error improvement of DA relative to OPL.
    
    value_ae = |ET_OPL - ET_REF| - |ET_DA - ET_REF|
    
    Positive values indicate DA agrees more closely with the reference than OPL.
    Negative values indicate DA degrades agreement relative to OPL.
    """
    return np.abs(et_opl - et_ref) - np.abs(et_da - et_ref)
