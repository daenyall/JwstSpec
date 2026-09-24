from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from DataPreprocess import DataPreprocessor
from DataAnalyzer import DataAnalyzer
from DataFetch import MastApiFetcher
from TransitCalculator import TransitCalculator
from PlanetParametersProvider import PlanetParametersProvider

import numpy as np

preprocessor = DataPreprocessor()
analyzer = DataAnalyzer()
fetcher = MastApiFetcher(base_path="./jwst_data")
calculate = TransitCalculator()
provider = PlanetParametersProvider()


target_name = "WASP-96b"


app = FastAPI(title="Spectrum API")

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])
@app.get("/")
def health_check():
    return {"status": "API działa", "version": "1.0"}

@app.get("/analyze")
def run_analysis(target: str = target_name):
    fits_data = fetcher.get_data(target)
    tobs = float(np.nanmedian(fits_data["TDB-MID"]))
    parameters = provider.get_parameters(target, tobs)
    t0 = parameters.get("t0")
    period_days = parameters.get("period_days")
    duration = parameters.get("duration_hours")
    mid_transit, transit_start, transit_end, duration_hours = calculate.calculate_transit_window(t0, period_days, duration, tobs)
    
    bins = preprocessor.extract_all_bins(fits_data, bin_width=0.03)
    spectrum = analyzer.calculate_binned_spectrum(bins, fits_data["TDB-MID"], transit_start, transit_end)

    return {
        "target": target,
        "spectrum": spectrum,
        "transit": {
            "midpoint": mid_transit,
            "start": transit_start,
            "end": transit_end,
            "duration_hours": duration_hours
        }
    }