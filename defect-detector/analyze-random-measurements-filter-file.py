import json
from collections import Counter

def read_ndjson(filename):
    """Read NDJSON file and return list of records."""
    records = []
    with open(filename, 'r') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

def circuit_params_to_tuple(params):
    """Convert circuit_params dict to hashable tuple for counting."""
    return tuple(sorted(params.items()))

def find_most_popular_params(records):
    """Find the most common circuit_params configuration."""
    params_counter = Counter()
    
    for record in records:
        if 'measurements' in record and 'circuit_params' in record['measurements']:
            params = record['measurements']['circuit_params']
            params_tuple = circuit_params_to_tuple(params)
            params_counter[params_tuple] = params_counter.get(params_tuple, 0) + 1
    
    # Get the most common params
    most_common = params_counter.most_common(1)[0]
    most_popular_params = dict(most_common[0])
    count = most_common[1]
    
    return most_popular_params, count

def filter_by_params(records, target_params):
    """Filter records that match the target circuit_params."""
    filtered = []
    
    for record in records:
        if 'measurements' in record and 'circuit_params' in record['measurements']:
            params = record['measurements']['circuit_params']
            if params == target_params:
                filtered.append(record)
    
    return filtered

def write_ndjson(filename, records):
    """Write records to NDJSON file."""
    with open(filename, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')

def main():
    input_file = 'defect-detector/random-measurements.json'
    output_file = 'defect-detector/filtered-random-measurements.json'
    
    # Read all records
    print(f"Reading {input_file}...")
    records = read_ndjson(input_file)
    print(f"Total records: {len(records)}")
    
    # Find most popular params
    print("\nFinding most popular circuit_params...")
    most_popular_params, count = find_most_popular_params(records)
    
    print(f"\nMost popular circuit_params (appears {count} times):")
    for key, value in most_popular_params.items():
        print(f"  {key}: {value}")
    
    # Filter records
    print(f"\nFiltering records...")
    filtered_records = filter_by_params(records, most_popular_params)
    print(f"Filtered records: {len(filtered_records)}")
    
    # Write output
    write_ndjson(output_file, filtered_records)
    print(f"\nFiltered data written to {output_file}")

if __name__ == "__main__":
    main()