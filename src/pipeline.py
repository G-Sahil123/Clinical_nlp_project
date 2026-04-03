import os
import json
from src.note_loader import load_notes 
from src.llm_client import call_llm
from src.clustering import cluster
from src.mapping import map_categories
from src.merge import merge
from utils.helpers import load_json,save_json    

def create_batches(notes, batch_size):
    for i in range(0, len(notes), batch_size):
        yield notes[i:i + batch_size]


def process_patient(patient_id, data_dir):
    patient_dir = os.path.join(data_dir,patient_id)

    notes = load_notes(patient_dir)     #(note_id,note_date,text)

    batches = list(create_batches(notes, batch_size=3))

    all_outputs = []

    for batch in batches:
        batch_input = []

        for note_id, note_date, text in batch:
            batch_input.append({
                "note_id": note_id,
                "note_date": note_date,
                "text": text
            })

        response = call_llm(f"Extract all condition mentions from the following batch of clinical notes {batch_input}")  
        try:
            result = json.loads(response)
            all_outputs.extend(result)
        except:
            print("Parsing failed")

    final_conditions, conditions_set = cluster(all_outputs)

    taxonomy = load_json(os.path.join(os.getcwd(),"..","taxonomy.json"))

    mapped_conditions = map_categories(conditions_set,taxonomy)

    merged_conditions = merge(final_conditions,mapped_conditions)


    result = {
        "patient_id":patient_id,
        "conditions":merged_conditions
    }

    return result

