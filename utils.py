# file converters
import json
import os


def save_jsonl(result, output_path):
    """Append a single result to the JSONL file."""
    with open(output_path, 'a') as f:
        f.write(json.dumps(result) + '\n')


def convert_jsonl_to_json(jsonl_path):
    """Convert JSONL file to JSON format."""
    json_path = jsonl_path.replace('.jsonl', '.json')
    results = []
    
    with open(jsonl_path, 'r') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Error on line {i}: {e}")
                print(f"Content: {repr(line[:100])}")  # Show first 100 chars
                raise  
    
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ Converted to JSON format: {json_path}")
    return json_path



def load_json_file(path):
    """Load a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r") as f:
        return json.load(f)
