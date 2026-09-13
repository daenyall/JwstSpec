from fastapi import FastAPI
from DataPreprocess import DataPreprocessor

target_name = "WASP-96b"
gases = {'H2O': 1.4, 'CH4': 2.3, 'CO2': 4.3}


app = FastAPI(title="JWST Spectrum API")

@app.get("/")
def health_check():
    return {"status": "API działa", "version": "1.0"}

@app.get("/analyze")
def run_analysis(target: str = target_name):
    preprocessor = DataPreprocessor.extract_all_gases()
    json_preprocessor = preprocessor.to_json()
    return json_preprocessor
