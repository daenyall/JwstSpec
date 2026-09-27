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


target_name = "WASP-39b"


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
    print("\n=== SNR BY WAVELENGTH BIN ===")

    bin_width = 0.03

    wavelengths = np.asarray(fits_data["WAVELENGTH"].iloc[0], dtype=float)
    flux_matrix = np.vstack(fits_data["FLUX"]).astype(float)
    error_matrix = np.vstack(fits_data["FLUX_ERROR"]).astype(float)

    finite_wavelengths = wavelengths[np.isfinite(wavelengths)]

    min_wavelength = np.nanmin(finite_wavelengths)
    max_wavelength = np.nanmax(finite_wavelengths)

    bin_start = min_wavelength
    snr_results = []

    while bin_start + bin_width <= max_wavelength:
        bin_end = bin_start + bin_width
        bin_center = bin_start + bin_width / 2

        mask = (wavelengths >= bin_start) & (wavelengths < bin_end)
        channels = int(mask.sum())

        if channels == 0:
            bin_start = bin_end
            continue

        flux_in_bin = flux_matrix[:, mask]
        error_in_bin = error_matrix[:, mask]

        binned_flux = np.nanmean(flux_in_bin, axis=1)
        binned_error = np.sqrt(np.nansum(error_in_bin ** 2, axis=1)) / channels

        valid = np.isfinite(binned_flux) & np.isfinite(binned_error) & (binned_error > 0)

        snr = np.full(len(binned_flux), np.nan)
        snr[valid] = np.abs(binned_flux[valid]) / binned_error[valid]

        median_snr = np.nanmedian(snr)
        median_flux = np.nanmedian(binned_flux)
        negative_fraction = np.mean(binned_flux < 0)

        snr_results.append({
            "bin_center": bin_center,
            "channels": channels,
            "median_snr": median_snr,
            "median_flux": median_flux,
            "negative_fraction": negative_fraction
        })

        bin_start = bin_end

    print("\nALL BINS:")

    for result in snr_results:
        print(
            f"λ={result['bin_center']:.4f} µm | "
            f"SNR={result['median_snr']:.2f} | "
            f"flux={result['median_flux']:.8f} | "
            f"negative={result['negative_fraction'] * 100:.1f}% | "
            f"channels={result['channels']}"
        )

    print("\n10 LOWEST-SNR BINS:")

    lowest_snr = sorted(snr_results, key=lambda result: result["median_snr"])

    for result in lowest_snr[:10]:
        print(
            f"λ={result['bin_center']:.4f} µm | "
            f"SNR={result['median_snr']:.2f} | "
            f"flux={result['median_flux']:.8f} | "
            f"negative={result['negative_fraction'] * 100:.1f}%"
        )

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