# JwstSpec

JwstSpec is a full-stack application for exploring transmission spectra of transiting exoplanets using public James Webb Space Telescope observations.

The application searches MAST for compatible JWST NIRISS/SOSS observations, downloads calibrated spectral products, determines the expected transit window using data from the NASA Exoplanet Archive, evaluates observation quality, and generates a wavelength-binned transmission spectrum.

## Features

- automatic JWST observation search through MAST
- NIRISS/SOSS observation filtering
- segmented `x1dints` product download and caching
- transit ephemeris retrieval from the NASA Exoplanet Archive
- wavelength binning
- flux and SNR quality checks
- temporal stability analysis
- linear light-curve detrending
- dataset-level quality validation
- transit depth calculation
- bootstrap uncertainty estimation
- FastAPI backend
- Next.js + TypeScript frontend
- interactive spectrum visualization with Recharts

## How it works

```text
Exoplanet name
      ↓
MAST search
      ↓
JWST NIRISS/SOSS observation
      ↓
x1dints products
      ↓
NASA Exoplanet Archive ephemeris
      ↓
Transit window
      ↓
Wavelength binning
      ↓
Quality checks
      ↓
Light-curve detrending
      ↓
Transit depth + uncertainty
      ↓
Transmission spectrum
```

Poor-quality observations are rejected before a spectrum is displayed, helping avoid presenting strongly unstable data as a reliable result.

## Example targets

The pipeline has been tested with targets including:

- WASP-39b
- WASP-96b
- HAT-P-18b
- WASP-17b

Not every target produces a spectrum. A target may have no compatible public NIRISS/SOSS observation, or the available observation may fail the quality checks.

## Quality checks

The pipeline evaluates individual wavelength bins using:

- median flux
- signal-to-noise ratio
- fraction of negative integrations
- out-of-transit scatter
- pre/post-transit baseline mismatch

Bins are classified as:

```text
valid
caution
rejected
```

The observation is also evaluated as a whole. If the dataset is too unstable, the API returns a poor-quality result instead of generating a spectrum.

## Tech stack

### Backend

- Python
- FastAPI
- NumPy
- Pandas
- Astropy
- Astroquery
- NASA Exoplanet Archive TAP API

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Recharts

## Project structure

```text
JwstSpec/
├── backend/
│   ├── api.py
│   ├── DataFetch.py
│   ├── DataPreprocess.py
│   ├── DataAnalyzer.py
│   ├── PlanetParametersProvider.py
│   ├── TransitCalculator.py
│   └── cache/
│       └── AnalysisCache.py
│
├── frontend/
│   └── app/
│       └── page.tsx
│
├── .gitignore
└── README.md
```

## Running locally

### Backend

```bash
cd backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python -m uvicorn api:app --reload
```

Backend:

```text
http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

## API

Analyze a target:

```text
GET /analyze?target=WASP-39b
```

The response contains the calculated spectrum, transit information, uncertainty estimates, and quality metadata.

The API also handles:

```text
404 — target not found
404 — no compatible NIRISS/SOSS observation
503 — MAST temporarily unavailable
```

## Scientific scope

The current pipeline focuses specifically on JWST NIRISS/SOSS observations.

It uses a simple linear baseline detrending model and estimates transit depth from median in-transit and out-of-transit flux. Uncertainty is estimated using bootstrap resampling.

It does not currently perform atmospheric retrieval, molecular abundance estimation, or full publication-grade instrument modeling.

Spectral features should not automatically be interpreted as detections of atmospheric molecules.

## Future improvements

- automated observation selection
- configurable wavelength bins
- automated tests
- improved detrending models
- correlated-noise estimation
- physical transit-model fitting
- additional JWST instruments
- comparison with published spectra