from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from DataPreprocess import DataPreprocessor
from DataAnalyzer import DataAnalyzer
from DataFetch import MastApiFetcher
from TransitCalculator import TransitCalculator
from PlanetParametersProvider import PlanetParametersProvider
from cache.AnalysisCache import AnalysisCache

import numpy as np

preprocessor = DataPreprocessor()
analyzer = DataAnalyzer()
fetcher = MastApiFetcher(base_path="./jwst_data")
calculate = TransitCalculator()
provider = PlanetParametersProvider()
cache = AnalysisCache()


target_name = "WASP-96b"


app = FastAPI(title="Spectrum API")

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])
@app.get("/")
def health_check():
    return {"status": "API działa", "version": "1.0"}

@app.get("/analyze")
def run_analysis(target: str = target_name):
    bin_width = 0.03

    cached_result = cache.get(target, bin_width)

    if cached_result is not None:
        print(f"Found cached data for {target}")
        return cached_result

    print(f"No cached data for {target}. Running analysis")

    fits_data = fetcher.get_data(target)

    tobs = float(np.nanmedian(fits_data["TDB-MID"]))

    parameters = provider.get_parameters(target, tobs)

    t0 = parameters["t0"]
    period_days = parameters["period_days"]
    duration_hours = parameters["duration_hours"]

    mid_transit, transit_start, transit_end, duration_hours = calculate.calculate_transit_window(t0, period_days, duration_hours, tobs)

    bins = preprocessor.extract_all_bins(fits_data, bin_width=bin_width)

    spectrum = analyzer.calculate_binned_spectrum(bins, fits_data["TDB-MID"], transit_start, transit_end)

    result = {
        "target": target,
        "spectrum": spectrum,
        "transit": {
            "midpoint": mid_transit,
            "start": transit_start,
            "end": transit_end,
            "duration_hours": duration_hours
        },
        "analysis": {
            "bin_width": bin_width,
            "ephemeris_reference": parameters["reference"],
            "ephemeris_time_system": parameters["time_system"],
            "duration_source": parameters["duration_source"]
        }
    }

    cache.save(target, bin_width, result)

    return result