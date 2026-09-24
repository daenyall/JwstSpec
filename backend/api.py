from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from DataPreprocess import DataPreprocessor
from DataAnalyzer import DataAnalyzer
from DataFetch import MastApiFetcher

preprocessor = DataPreprocessor()
analyzer = DataAnalyzer()
fetcher = MastApiFetcher(base_path="./jwst_data")

target_name = "WASP-96b"

mid_transit = 2459751.82468
duration_hours = 2.4264
duration_days = duration_hours / 24
half_duration = duration_days / 2

midpoint = mid_transit - 2400000.5
transit_start = midpoint - half_duration
transit_end = midpoint + half_duration

app = FastAPI(title="Spectrum API")

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])
@app.get("/")
def health_check():
    return {"status": "API działa", "version": "1.0"}

@app.get("/analyze")
def run_analysis(target: str = target_name):
    fits_data = fetcher.get_data(target)

    bins = preprocessor.extract_all_bins(fits_data, bin_width=0.03)
    spectrum = analyzer.calculate_binned_spectrum(bins, fits_data["TDB-MID"], transit_start, transit_end)

    return {
        "target": target,
        "spectrum": spectrum,
        "transit": {
            "midpoint": midpoint,
            "start": transit_start,
            "end": transit_end,
            "duration_hours": duration_hours
        }
    }