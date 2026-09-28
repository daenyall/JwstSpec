from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from DataPreprocess import DataPreprocessor
from DataAnalyzer import DataAnalyzer
from DataFetch import MastApiFetcher, MastServiceUnavailableError
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def health_check():
    return {
        "status": "API działa",
        "version": "1.0"
    }


@app.get("/analyze")
def run_analysis(target: str = target_name):
    bin_width = 0.03

    cached_result = cache.get(
        target,
        bin_width
    )

    if cached_result is not None:
        print(f"Found cached data for {target}")
        return cached_result

    print(f"No cached data for {target}. Running analysis")

    try:
        fits_data = fetcher.get_data(target)

    except MastServiceUnavailableError as error:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "mast_unavailable",
                "message": str(error)
            }
        ) from error

    except ValueError as error:
        message = str(error)

        if message.startswith("No MAST observations found"):
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "target_not_found",
                    "message": message
                }
            ) from error

        if (
            "No JWST NIRISS/SOSS observations found" in message
            or "No segmented NIRISS/SOSS x1dints products found" in message
        ):
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "no_compatible_observation",
                    "message": (
                        "No compatible public JWST NIRISS/SOSS observation "
                        "was found for this target."
                    )
                }
            ) from error

        raise

    tobs = float(
        np.nanmedian(
            fits_data["TDB-MID"]
        )
    )

    parameters = provider.get_parameters(
        target,
        tobs
    )

    t0 = parameters["t0"]
    period_days = parameters["period_days"]
    duration_hours = parameters["duration_hours"]

    (
        mid_transit,
        transit_start,
        transit_end,
        duration_hours
    ) = calculate.calculate_transit_window(
        t0,
        period_days,
        duration_hours,
        tobs
    )

    bins = preprocessor.extract_all_bins(
        fits_data,
        bin_width=bin_width
    )

    times = np.asarray(
        fits_data["TDB-MID"],
        dtype=float
    )

    dataset_quality = analyzer.evaluate_dataset_quality(
        bins,
        times,
        transit_start,
        transit_end
    )

    print("\n=== DATASET QUALITY ===")
    print(
        f"Status: "
        f"{dataset_quality['status']}"
    )

    if dataset_quality["median_oot_scatter"] is not None:
        print(
            f"Median OOT scatter: "
            f"{dataset_quality['median_oot_scatter'] * 100:.4f}%"
        )

    if dataset_quality["median_baseline_mismatch"] is not None:
        print(
            f"Median baseline mismatch: "
            f"{dataset_quality['median_baseline_mismatch'] * 100:.4f}%"
        )

    print(
        f"Bins evaluated: "
        f"{dataset_quality['bins_evaluated']}"
    )

    if dataset_quality["reasons"]:
        print(
            f"Reasons: "
            f"{', '.join(dataset_quality['reasons'])}"
        )

    if dataset_quality["status"] == "poor":
        return {
            "target": target,
            "spectrum": [],
            "transit": {
                "midpoint": mid_transit,
                "start": transit_start,
                "end": transit_end,
                "duration_hours": duration_hours
            },
            "analysis": {
                "status": "poor_quality",
                "message": (
                    "The observation quality is too poor to produce "
                    "a reliable transmission spectrum with the current pipeline."
                ),
                "bin_width": bin_width,
                "dataset_quality": dataset_quality,
                "ephemeris_reference": parameters.get("reference"),
                "time_system": parameters.get("time_system"),
                "duration_source": parameters.get("duration_source")
            }
        }

    spectrum = analyzer.calculate_binned_spectrum(
        bins,
        fits_data["TDB-MID"],
        transit_start,
        transit_end
    )

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
            "status": "success",
            "bin_width": bin_width,
            "dataset_quality": dataset_quality,
            "ephemeris_reference": parameters.get("reference"),
            "time_system": parameters.get("time_system"),
            "duration_source": parameters.get("duration_source")
        }
    }

    cache.save(
        target,
        bin_width,
        result
    )

    return result