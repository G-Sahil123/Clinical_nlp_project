from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from utils.helpers import save_json
from llm_client import call_llm
import re
import os
import json

from dateutil import parser


def normalize_onset_date(date_str):
    if not date_str:
        return None
    try:
        # Try parsing the date with fuzzy logic
        dt = parser.parse(date_str, fuzzy=True, dayfirst=True)
        
        # Decide format based on which components exist in the original string
        digits = [int(s) for s in date_str.replace("/", " ").split() if s.isdigit()]
        if len(digits) == 3:
            # Day, Month, Year -> Full date
            return dt.strftime("%d %B %Y")
        elif len(digits) == 2:
            # Month & Year
            return dt.strftime("%B %Y")
        elif len(digits) == 1:
            # Only year
            return dt.strftime("%Y")
        else:
            # Fallback
            return dt.strftime("%d %B %Y")
    except:
        return None
    
def get_cluster_status(status_list):
    if "resolved" in status_list:
        return "resolved"
    elif "active" in status_list:
        return "active"
    else:
        return "suspected"


def cluster(dataset):

    all_candidates = []
    conditions_set = {}

    for data in dataset:
        for c in data["candidates"]:
            all_candidates.append({
                "note_id": data["note_id"],
                "line_no": c["line_no"],
                "span": c["span"],
                "status_hint": c["status_hint"],
                "note_date": data["note_date"],
                "date_mention": c["date_mention"]
            })

    spans = [c["span"] for c in all_candidates]

    model = SentenceTransformer('all-mpnet-base-v2')  # or a medical variant like 'pritamdeka/BioBERT-mnli-snli-sentence-transformer'
    embeddings = model.encode(spans)

    clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=1.0, linkage='average')
    labels = clustering.fit_predict(embeddings)

    clustered_conditions = {}
    for idx, label in enumerate(labels):
        if label not in clustered_conditions:
            clustered_conditions[label] = {
                "condition_names": [],
                "evidence": [],
                "status_list": [],
                "date_mentions": [],
                "note_dates": []
            }
        clustered_conditions[label]["condition_names"].append(spans[idx])
        clustered_conditions[label]["evidence"].append({
            "note_id": all_candidates[idx]["note_id"],
            "line_no": all_candidates[idx]["line_no"],
            "span": spans[idx]
        })
        clustered_conditions[label]["status_list"].append(all_candidates[idx]["status_hint"])
        clustered_conditions[label]["date_mentions"].append(all_candidates[idx].get("date_mention"))
        clustered_conditions[label]["note_dates"].append(all_candidates[idx].get("note_date"))
    all_cluster_members = [c["condition_names"] for c in clustered_conditions.values()]

    raw_output = call_llm(
    f"""
        You are given a list of clusters, each cluster is a list of clinical condition mentions.
        For each cluster, provide a **single canonical name** that best represents all items in that cluster.
        Make names simple, clinically meaningful, and concise.
        Return only a JSON list of canonical names, one for each cluster, in the same order.
        **Return only a JSON array of strings, nothing else.**
        
        Example input: [["fever", "high temperature"], ["cough", "dry cough"]]
        Example output: ["Fever", "Cough"]
        
        Input clusters: {all_cluster_members}
    """
    )
    if not raw_output:
        raise ValueError("LLM returned empty output!")

    clean_output = re.sub(r"^```(?:json)?|```$", "", raw_output.strip())
    canonical_names_list = json.loads(clean_output)
    # print(all_cluster_members)
        
    final_conditions = []
    for cluster, canonical_name in zip(clustered_conditions.values(), canonical_names_list):
        conditions_set[canonical_name] = {
            "category": None,
            "subcategory": None
        }
        sorted_evidence = sorted(cluster["evidence"], key=lambda x:(x["note_id"],x["line_no"]))
        onset_dates_raw = [d for d in cluster["date_mentions"] if d] + [d for d in cluster["note_dates"] if d]

        if onset_dates_raw:
            normalized_dates = [normalize_onset_date(d) for d in onset_dates_raw if normalize_onset_date(d)]
            if normalized_dates:
                onset_date = min(normalized_dates, key=lambda x: parser.parse(x, fuzzy=True))
            else:
                onset_date = None
        else:
            onset_date = None
        final_conditions.append({
            "condition_name": canonical_name,
            "status": get_cluster_status(cluster["status_list"]),
            "onset_date": onset_date,
            "evidence": sorted_evidence
        })

    return final_conditions, conditions_set

