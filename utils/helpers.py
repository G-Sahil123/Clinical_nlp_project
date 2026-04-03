import json

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"JSON saved to {file_path}")

def load_json(file_path):
    with open(file_path) as f:
        file = json.load(f)
    return file