# Clinical NLP Pipeline

## 📌 Overview
This project implements a Clinical NLP pipeline that processes patient notes and extracts structured medical condition data. The pipeline performs:

1. Condition Extraction  
2. Normalization & Clustering  
3. Category Mapping (based on taxonomy)  

The system is built as a modular CLI-based pipeline using an OpenAI-compatible API.

---

## 🏗️ Project Structure

project/
│── main.py # CLI entrypoint
│── requirements.txt # Dependencies
│── utils/
│ ├── helpers
├── src 
│ ├── clustering.py # LLM API calls
│ ├── llm_client.py
│ ├── mapping.py # LLM API calls
│ ├── note_loader.py
│ ├── merge.py # LLM API calls
│ ├── pipeline.py
│── data/
│── output/