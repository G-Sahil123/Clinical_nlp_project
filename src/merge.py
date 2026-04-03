

# Load files
def merge(final_conditions,mapped_conditions):

    conditions = final_conditions
    mapping = mapped_conditions


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


