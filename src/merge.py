from utils.helpers import save_json,load_json
import os

# Load files
def merge(path1:str,path2:str):

    conditions = load_json(path1)
    mapping = load_json(path2)


    merged_conditions = []
    # 🔹 Merge
    for condition in conditions:
        name = condition["condition_name"]
        if name in mapping.keys():
            category = mapping[name]["category"]
            subcategory = mapping[name]["subcategory"]
        else:
            category = "Unknown"
            subcategory = "Unknown"
        
        new_condition = {
            "condition_name": name,
            "category": category,
            "subcategory": subcategory,
            "status": condition.get("status"),
            "onset_date": condition.get("onset_date"),
            "evidence": condition.get("evidence")
        }

        merged_conditions.append(new_condition)
    
    return merged_conditions


