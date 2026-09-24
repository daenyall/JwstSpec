import numpy as np

class DataPreprocessor:

    def extract_binned_lightcurve(self, raw_table, bin_center: float, bin_width: float = 0.03):
        waves = np.array(raw_table["WAVELENGTH"][0], dtype=float)

        half_width = bin_width / 2
        bin_start = bin_center - half_width
        bin_end = bin_center + half_width

        wavelength_mask = (waves >= bin_start) & (waves < bin_end)
        channels_in_bin = np.count_nonzero(wavelength_mask)

        if not wavelength_mask.any():
            return None

        flux_matrix = np.vstack(raw_table["FLUX"]).astype(float)
        flux_in_bin = flux_matrix[:, wavelength_mask]

        binned_flux = np.nanmean(flux_in_bin, axis=1)
        normalized_flux = binned_flux / np.nanmedian(binned_flux)

        return {
            "bin_start": float(bin_start),
            "bin_center": float(bin_center),
            "bin_end": float(bin_end),
            "channels": int(channels_in_bin),
            "lightcurve": normalized_flux
        }

    def extract_all_bins(self, raw_table, bin_width: float = 0.03):
        waves = np.array(raw_table["WAVELENGTH"][0], dtype=float)
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