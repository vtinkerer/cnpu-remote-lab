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

def filter_signal_fft(signal, time):
    # Calculate FFT
    fft_values = np.fft.fft(signal)
    fft_freq = np.fft.fftfreq(len(signal), d=(time[1] - time[0]))

    cutoff_frequency = 0.4 # MHz - adjust this value as needed

    # Filter: Keep only frequencies below a cutoff
    fft_filtered = fft_values.copy()
    fft_filtered[np.abs(fft_freq) > cutoff_frequency] = 0

    # Reconstruct signal using inverse FFT
    reconstructed_signal = np.fft.ifft(fft_filtered).real
    return reconstructed_signal

def filter_signal(signal, signal_type):
    window_width = 0
    if signal_type == 'current':
        window_width = 17  # Wider window for current to remove spikes
    elif signal_type == 'voltage':
        window_width = 8   # Narrower window for voltage to preserve details
    else:
        raise ValueError("signal_type must be 'current' or 'voltage'")
     
    pad_width = window_width // 2
    signal_padded = np.pad(signal, (pad_width, 0), mode='reflect')  # Left: reflect
    signal_padded = np.pad(signal_padded, (0, pad_width), mode='edge')  # Right: edge

    filtered_signal = np.median(
        np.lib.stride_tricks.sliding_window_view(
            signal_padded, window_width
        ),
        axis=1
    )

    # Apply second pass of filtering to the left portion
    left_portion_len = round(len(signal) * (40 / 620))  # Filter first part of signal
    left_window = window_width * 2  # Double the window for left side
    left_pad_width = left_window // 2
    left_padded = np.pad(signal[:left_portion_len + left_pad_width], 
                         (left_pad_width, left_pad_width), mode='reflect')
    filtered_signal[:left_portion_len] = np.median(
        np.lib.stride_tricks.sliding_window_view(left_padded, left_window),
        axis=1
    )[:left_portion_len]

    return filtered_signal
