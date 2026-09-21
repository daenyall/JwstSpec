from fastapi import FastAPI
from DataPreprocess import DataPreprocessor
from DataAnalyzer import DataAnalyzer
from DataFetch import MastApiFetcher
from fastapi.middleware.cors import CORSMiddleware

preprocessor = DataPreprocessor()
analyzer = DataAnalyzer()
fetcher = MastApiFetcher(base_path="./jwst_data")

target_name = "WASP-96b"
gases = {'H2O': 1.4, 'CH4': 2.3, 'CO2': 4.3}

#time in days
mid_transit = 2459751.82468
duration = 2.4264 / 24
half_duration = duration / 2
midpoint = mid_transit - 2400000.5
transit_start = midpoint - half_duration
transit_end = midpoint + half_duration

app = FastAPI(title="Spectrum API")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])
@app.get("/")
def health_check():
    return {"status": "API działa", "version": "1.0"}

@app.get("/analyze")
def run_analysis(target: str = target_name):
    fits_data = fetcher.get_data(target)
    preprocessed_data = preprocessor.extract_all_gases(fits_data, gases)
    analysis_result = analyzer.calculate_transit_depth(preprocessed_data, transit_start, transit_end, gases)
    lightcurves_data = preprocessed_data.to_dict(orient='records')
    results = {"target": target, "lightcurves": lightcurves_data, "analysis": analysis_result}
    return results



  
