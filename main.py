import os
import json
import argparse
from src.pipeline import process_patient
from utils.helpers import save_json

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--patient-list", required=True)
    parser.add_argument("--output-dir", required=True)

    return parser.parse_args()

def create_batches(notes, batch_size):
    for i in range(0, len(notes), batch_size):
        yield notes[i:i + batch_size]

def main():

    args = parse_args()

    with open(args.patient_list,"r") as f:
        patient_ids = json.load(f)

    os.makedirs(args.output_dir, exist_ok=True)

    for patient_id in patient_ids:
        print(f"Processing {patient_id}...")

        result = process_patient(
            patient_id = patient_id,
            data_dir = args.data_dir
        )

        output_path = os.path.join(args.output_dir, f"{patient_id}.json")

        save_json(result,output_path)

    print("✅ Done!")

if __name__ == "__main__":
    main()
