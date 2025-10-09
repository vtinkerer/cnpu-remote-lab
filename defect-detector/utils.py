import numpy as np


def fix_signal_spike(signal, extrapolate_percent=5, reference_start=5, reference_end=10):
    """
    Fix spike at beginning of signal by extrapolating from a stable reference region.
    
    Parameters:
    -----------
    signal : array-like
        Input signal with spike at beginning
    extrapolate_percent : float
        Percentage of signal length to replace (default: 5%)
    reference_start : float
        Start of reference region as percentage of signal length (default: 5%)
    reference_end : float
        End of reference region as percentage of signal length (default: 10%)

    Returns:
    --------
    corrected_signal : numpy array
        Signal with corrected beginning
    """
    signal = np.array(signal)
    n = len(signal)
    
    # Calculate indices
    replace_end = int(n * extrapolate_percent / 100)
    ref_start = int(n * reference_start / 100)
    ref_end = int(n * reference_end / 100)
    
    # Extract reference region for extrapolation
    ref_indices = np.arange(ref_start, ref_end)
    ref_values = signal[ref_start:ref_end]
    
    # Fit polynomial to reference region (linear or quadratic)
    # Try linear first, then quadratic if needed
    try:
        # Linear fit
        coeffs = np.polyfit(ref_indices, ref_values, 1)
        poly_func = np.poly1d(coeffs)
    except:
        # Fallback to mean if fitting fails
        poly_func = lambda x: np.mean(ref_values)
    
    # Generate extrapolated values for the beginning
    replace_indices = np.arange(0, replace_end)
    extrapolated_values = poly_func(replace_indices)
    
    # Create corrected signal
    corrected_signal = signal.copy()
    corrected_signal[:replace_end] = extrapolated_values
    
    # Smooth the transition to avoid discontinuity
    transition_length = min(20, replace_end // 2)
    if transition_length > 0:
        transition_start = replace_end - transition_length
        transition_end = replace_end + transition_length
        
        # Create smooth transition using cosine taper
        taper = np.linspace(0, np.pi, 2 * transition_length)
        weight = (1 + np.cos(taper)) / 2
        
        # Apply transition weights
        for i in range(transition_length):
            idx = transition_start + i
            if idx < len(corrected_signal):
                original_weight = 1 - weight[i]
                extrapolated_weight = weight[i]
                corrected_signal[idx] = (original_weight * signal[idx] + 
                                       extrapolated_weight * extrapolated_values[idx])
    
    return corrected_signal


def henries_to_femtohenries(henries):
    return f"{int(henries * 1e15)}fH"


def farads_to_femtofarads(farads):
    return f"{int(farads * 1e15)}fF"


def trim_data_for_calculations(data_array):
    """Trim 10% from beginning and end of data for calculations"""
    n = len(data_array)
    trim_size = n // 10
    if trim_size == 0:  # Handle small datasets
        return data_array
    return data_array[trim_size:-trim_size]