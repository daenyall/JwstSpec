import numpy as np

class DataPreprocessor:

    def extract_binned_lightcurve(self, raw_table, bin_center, bin_width=0.03):
        wavelengths = np.asarray(raw_table["WAVELENGTH"].iloc[0], dtype=float)

        half_width = bin_width / 2
        bin_start = bin_center - half_width
        bin_end = bin_center + half_width

        wavelength_mask = (wavelengths >= bin_start) & (wavelengths < bin_end)
        channels = int(wavelength_mask.sum())

        if channels == 0:
            return None

        flux_matrix = np.vstack(raw_table["FLUX"].to_numpy()).astype(float)
        flux_in_bin = flux_matrix[:, wavelength_mask]

        valid_flux_counts = np.sum(np.isfinite(flux_in_bin), axis=1)
        flux_sum = np.nansum(flux_in_bin, axis=1)

        binned_flux = np.divide(
            flux_sum,
            valid_flux_counts,
            out=np.full(len(flux_sum), np.nan, dtype=float),
            where=valid_flux_counts > 0
        )

        median_flux = float(np.nanmedian(binned_flux))

        finite_flux = np.isfinite(binned_flux)

        if np.any(finite_flux):
            negative_fraction = float(np.mean(binned_flux[finite_flux] < 0))
        else:
            negative_fraction = 1.0

        median_snr = None

        if "FLUX_ERROR" in raw_table.columns:
            error_matrix = np.vstack(raw_table["FLUX_ERROR"].to_numpy()).astype(float)
            error_in_bin = error_matrix[:, wavelength_mask]

            valid_error_counts = np.sum(np.isfinite(error_in_bin), axis=1)
            error_sum_squared = np.nansum(error_in_bin ** 2, axis=1)

            binned_error = np.divide(
                np.sqrt(error_sum_squared),
                valid_error_counts,
                out=np.full(len(error_sum_squared), np.nan, dtype=float),
                where=valid_error_counts > 0
            )

            valid_snr = np.isfinite(binned_flux) & np.isfinite(binned_error) & (binned_error > 0)

            snr = np.full(len(binned_flux), np.nan, dtype=float)
            snr[valid_snr] = np.abs(binned_flux[valid_snr]) / binned_error[valid_snr]

            if np.any(np.isfinite(snr)):
                median_snr = float(np.nanmedian(snr))

        quality_status, quality_reasons = self._classify_bin_quality(
            median_flux,
            median_snr,
            negative_fraction
        )

        normalized_flux = None

        if quality_status != "rejected":
            normalized_flux = binned_flux / median_flux

        return {
            "bin_start": bin_start,
            "bin_center": bin_center,
            "bin_end": bin_end,
            "channels": channels,
            "lightcurve": normalized_flux,
            "median_flux": median_flux,
            "median_snr": median_snr,
            "negative_fraction": negative_fraction,
            "quality_status": quality_status,
            "quality_reasons": quality_reasons
        }

    
    def extract_all_bins(self, raw_table, bin_width: float = 0.03):
        waves = np.asarray(raw_table["WAVELENGTH"].iloc[0], dtype=float)
        valid_waves = waves[np.isfinite(waves)]

        min_wave = np.min(valid_waves)
        max_wave = np.max(valid_waves)

        bins = []
        bin_start = min_wave

        while bin_start + bin_width <= max_wave:
            bin_end = bin_start + bin_width
            bin_center = (bin_start + bin_end) / 2

            extracted_bin = self.extract_binned_lightcurve(raw_table, bin_center=bin_center, bin_width=bin_width)

            if extracted_bin is not None:
                bins.append(extracted_bin)

            bin_start = bin_end

        return bins

    
    def _classify_bin_quality(self, median_flux, median_snr, negative_fraction):
        rejected_reasons = []

        if not np.isfinite(median_flux) or median_flux <= 0:
            rejected_reasons.append("non-positive median flux")

        if median_snr is not None and np.isfinite(median_snr) and median_snr < 20:
            rejected_reasons.append("SNR below 20")

        if negative_fraction > 0.10:
            rejected_reasons.append("more than 10% negative integrations")

        if rejected_reasons:
            return "rejected", rejected_reasons

        caution_reasons = []

        if median_snr is None or not np.isfinite(median_snr):
            caution_reasons.append("SNR unavailable")
        elif median_snr < 50:
            caution_reasons.append("SNR below 50")

        if negative_fraction > 0.01:
            caution_reasons.append("more than 1% negative integrations")

        if caution_reasons:
            return "caution", caution_reasons
        return "valid", []

        