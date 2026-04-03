import json
from llm_client import call_llm
import re

TAXONOMY_RULES = {
    "carcinoma": ("cancer", "primary_malignancy"),
    "oral thrush": ("infectious", "fungal"),
    "Aortic sclerosis": ("cardiovascular", "vascular"),
    "Hypacusis": ("neurological", "functional"),
    "Lymphopenia": ("hematoogical", "cytopenia"),
    "Degenerative": ("musculoskeletal", "degenerative"),
    "Polyposis coli": ("cancer", "pre_malignant"),
    "Renal cysts": ("renal", "structural"),
    "Calcified pulmonary granuloma": ("infectious", "bacterial"),
    "Cerebral infracts": ("neurological","cerebovascular"),
    "Malresorptive hydrocephalus": ("neurological", "cerebrovascular"),
    "Rhabdomyolysis": ("musculoskeletal", "connective_tissue_disorder"),
    "Ventriculitis": ("infectious", "bacterial"),
    "Cerebral edema": ("neurological", "traumatic"),
    "nerve palsy": ("neurological", "traumatic"),
    "Subdural hematoma": ("neurological", "traumatic"),
    "Propofol infusion syndrome": ("toxicological", "poisoning"),
    "Bilateral disc swelling": ("neurological", "traumatic"),
    "Pulmonary aspergillosis": ("infectious", "fungal"),
    "Staphylococcus epidermidis": ("infectious", "bacterial"),
    "Thrombophlebitis": ("cardiovascular", "inflammatory_vascular"),
    "Rheumatoid arthritis": ("immunological", "autoimmune"),
    "Uveitis": ("immunological", "autoimmune"),
    "myocarditis": ("cardiovascular", "inflammatory_vascular"),
    "Bilateral pneumonia": ("infectious", "viral"),
    "foramen ovale": ("cardiovascular", "structural")

}


def rule_based_mapping(condition_name):
    name = condition_name.lower()

    for key in TAXONOMY_RULES:
        if key in name:
            return {
                "category": TAXONOMY_RULES[key][0],
                "subcategory": TAXONOMY_RULES[key][1],
                # "confidence": "high"
            }

    return None


def validate_mapping(cond, taxonomy):
    cat = cond.get("category")
    sub = cond.get("subcategory")

    if cat not in taxonomy:
        return False

    if sub not in taxonomy[cat]["subcategories"]:
        return False

    return True


def llm_map(conditions, taxonomy_text):
    prompt = f"""
You are a clinical NLP system.

Map each condition to EXACTLY one category and subcategory from the taxonomy.

STRICT RULES:
- Use ONLY given taxonomy categories and subcategories
- Do NOT invent categories
- Choose closest valid match if unsure 
- Do not return unknown
- Output ONLY valid JSON
- Do NOT include explanations
- Do not disturb evidence,status or onset_date,just on the basis of condition_name map the category and subcategory.
- Do NOT include markdown
- Do NOT include ```json
- Return COMPLETE JSON array
- Ensure JSON is syntactically valid (closing brackets required)
- take care of diambiguiation rule and notes as well

TAXONOMY:
{taxonomy_text}

INPUT:
{json.dumps(conditions, indent=2)}

OUTPUT:
You have to return JSON list like thsi as demonstrated by the example below.
- condition_name
- category
- subcategory

Example:
[
  {{
    "condition_name": "Tongue Base Carcinoma",
    "category": "cancer",
    "subcategory": "primary_malignancy"
  }}
]

The format will be just like above for every condition
"""

    response = call_llm(prompt)
    print("RAW LLM RESPONSE:\n", response)

    try:
        return json.loads(response)
    except:
        return []


def map_categories(conditions, taxonomy):
    """
    conditions: list of condition dicts (without category)
    taxonomy: loaded taxonomy.json
    """
    taxonomy_dict = taxonomy["condition_categories"]

    mapped_conditions = {}
    llm_needed = {}

    for condition_name, details in conditions.items():
        mapping = rule_based_mapping(condition_name)

        if mapping:
            details["category"] = mapping["category"]
            details["subcategory"] = mapping["subcategory"]
            # cond["mapping_confidence"] = mapping["confidence"]
            mapped_conditions[condition_name] = details
        else:
            llm_needed[condition_name] = details

    if llm_needed:
        taxonomy_text = json.dumps(taxonomy_dict, indent=2)
        llm_input = [
            {"condition_name": name}
            for name in llm_needed.keys()
        ]
        llm_results = llm_map(llm_input, taxonomy_text)

        for condition_name, details in llm_needed.items():
            match = next(
                (x for x in llm_results if x["condition_name"] == condition_name),
                None
            )

            if match:
                details["category"] = match.get("category")
                details["subcategory"] = match.get("subcategory")
                    # cond["mapping_confidence"] = "medium"
            else:
                details["category"] = "unknown"
                details["subcategory"] = "unknown"
                # cond["mapping_confidence"] = "low"

            mapped_conditions[condition_name] = details

    final_conditions = {}

    for condition_name, details in mapped_conditions.items():
        cond_obj = {
            "condition_name": condition_name,
            "category": details.get("category"),
            "subcategory": details.get("subcategory")
        }

        if validate_mapping(cond_obj, taxonomy_dict):
            final_conditions[condition_name] = details
        else:
            retry = retry_single_condition(cond_obj, taxonomy_dict)

            if retry and validate_mapping(retry, taxonomy_dict):
                final_conditions[condition_name] = {
                    "category": retry["category"],
                    "subcategory": retry["subcategory"]
                }
            else:
                final_conditions[condition_name] = {
                    "category": "Unknown",
                    "subcategory": "Unknown"
                }

    return final_conditions

def retry_single_condition(cond, taxonomy_dict):
    prompt = f"""
Map this condition strictly to taxonomy.

Condition:
{cond["condition_name"]}

Taxonomy:
{json.dumps(taxonomy_dict, indent=2)}

Return JSON:
{{
  "condition_name": "{cond["condition_name"]}",
  "category": "...",
  "subcategory": "..."
}}
"""

    response = call_llm(prompt)

    try:
        data = json.loads(response)
        return data
    except:
        return None



