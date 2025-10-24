import json
import numpy as np
from .utils import filter_signal, fix_signal_spike

def load_ndjson_file(filepath):
    """Load newline-delimited JSON data from file"""
    measurements = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():  # Skip empty lines
                measurements.append(json.loads(line))
    return measurements

def save_ndjson_file(filepath, data):
    """Save data as newline-delimited JSON to file"""
    with open(filepath, 'w') as f:
        for entry in data:
            f.write(json.dumps(entry) + '\n')
 

def filter_current_in_raw(current):
    return filter_signal(current, 'current')

def filter_voltage_in_raw(voltage):
    return filter_signal(voltage, 'voltage')

data = load_ndjson_file('defect-detector/raw-measurements.json')
for entry in data:
    raw_current = np.asarray(entry['measurements']['current'])
    corrected_current = filter_current_in_raw(raw_current)
    entry['measurements']['current'] = corrected_current.tolist()
    raw_voltage = np.asarray(entry['measurements']['voltage'])
    corrected_voltage = filter_voltage_in_raw(raw_voltage)
    entry['measurements']['voltage'] = corrected_voltage.tolist()

save_ndjson_file('defect-detector/filtered-raw-measurements.json', data)