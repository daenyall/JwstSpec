import numpy as np
class DataAnalyzer:

    def calculate_transit_depth(self, lightcurve_data_df, transit_start, transit_end, gases):
        in_transit_mask = (
        (lightcurve_data_df["TDB-MID"] >= transit_start) & 
        (lightcurve_data_df["TDB-MID"] <= transit_end))

        in_transit = lightcurve_data_df[in_transit_mask]
        out_of_transit = lightcurve_data_df[~in_transit_mask]
        print(f"ROWS IN:{len(in_transit.index)} ")
        print(f"ROWS OUT:{len(out_of_transit.index)} ")

        results = {}
        
        for gas in gases.keys():

            if gas in lightcurve_data_df.columns:
                in_transit_median = np.nanmedian(in_transit[gas])
                out_of_transit_median = np.nanmedian(out_of_transit[gas])
                depth = (out_of_transit_median - in_transit_median) / out_of_transit_median
                results[gas] = {"in_transit_median": in_transit_median, "out_of_transit_median": out_of_transit_median, "depth": depth}
        return results

    def calculate_binned_spectrum(self, bins, tdb_mid, transit_start, transit_end):
        times = np.asarray(tdb_mid, dtype=float)

        in_transit_mask = (times >= transit_start) & (times <= transit_end)
        out_of_transit_mask = ~in_transit_mask

        rng = np.random.default_rng(42)
        spectrum = []

        for bin_data in bins:
            quality_status = bin_data.get("quality_status", "valid")

            if quality_status == "rejected":
                continue

            if bin_data.get("lightcurve") is None:
                continue

            lightcurve = np.asarray(bin_data["lightcurve"], dtype=float)

            if len(lightcurve) != len(times):
                raise ValueError("Lightcurve length does not match TDB-MID length")

            detrended_lightcurve = self.detrend_lightcurve(
                times,
                lightcurve,
                transit_start,
                transit_end
            )

            if detrended_lightcurve is None:
                continue
            if detrended_lightcurve is None:
                continue

            temporal_quality = self.classify_temporal_quality(
                detrended_lightcurve,
                times,
                transit_start,
                transit_end
            )

            if temporal_quality["status"] == "rejected":
                continue

            in_flux = detrended_lightcurve[in_transit_mask]
            out_flux = detrended_lightcurve[out_of_transit_mask]

            in_flux = in_flux[np.isfinite(in_flux)]
            out_flux = out_flux[np.isfinite(out_flux)]

            if len(in_flux) == 0 or len(out_flux) == 0:
                continue

            in_median = np.nanmedian(in_flux)
            out_median = np.nanmedian(out_flux)

            if not np.isfinite(out_median) or abs(out_median) < 1e-12:
                continue

            depth = (out_median - in_median) / out_median

            bootstrap_depths = []

            for _ in range(1000):
                in_sample = rng.choice(in_flux, size=len(in_flux), replace=True)
                out_sample = rng.choice(out_flux, size=len(out_flux), replace=True)

                sample_in_median = np.nanmedian(in_sample)
                sample_out_median = np.nanmedian(out_sample)

                if not np.isfinite(sample_out_median) or abs(sample_out_median) < 1e-12:
                    continue

                bootstrap_depth = (sample_out_median - sample_in_median) / sample_out_median
                bootstrap_depths.append(bootstrap_depth)

            if len(bootstrap_depths) < 2:
                uncertainty = np.nan
            else:
                uncertainty = np.nanstd(bootstrap_depths, ddof=1)

            spectrum.append({
                "bin_start": bin_data["bin_start"],
                "bin_center": bin_data["bin_center"],
                "bin_end": bin_data["bin_end"],
                "channels": bin_data["channels"],
                "in_transit_median": float(in_median),
                "out_of_transit_median": float(out_median),
                "depth": float(depth),
                "uncertainty": float(uncertainty),
                "quality_status": quality_status,
                "quality_reasons": bin_data.get("quality_reasons", []),
                "median_snr": bin_data.get("median_snr"),
                "negative_fraction": bin_data.get("negative_fraction"),
                "temporal_quality_status": temporal_quality["status"],
                "oot_scatter": temporal_quality["oot_scatter"],
                "baseline_mismatch": temporal_quality["baseline_mismatch"],
                "temporal_quality_reasons": temporal_quality["reasons"]
            })

        return spectrum

    def detrend_lightcurve(self, times, lightcurve, transit_start, transit_end):
        times = np.asarray(times, dtype=float)
        lightcurve = np.asarray(lightcurve, dtype=float)

        if len(times) != len(lightcurve):
            raise ValueError("Times and lightcurve must have the same length")

        finite_mask = np.isfinite(times) & np.isfinite(lightcurve)

        out_of_transit_mask = finite_mask & (
            (times < transit_start) | (times > transit_end)
        )

        if np.sum(out_of_transit_mask) < 2:
            return None

        out_times = times[out_of_transit_mask]
        out_flux = lightcurve[out_of_transit_mask]

        reference_time = np.nanmedian(out_times)

        centered_out_times = out_times - reference_time
        centered_times = times - reference_time

        slope, intercept = np.polyfit(centered_out_times, out_flux, 1)

        baseline = slope * centered_times + intercept

        valid_baseline = np.isfinite(baseline) & (np.abs(baseline) > 1e-12)

        detrended = np.full(len(lightcurve), np.nan, dtype=float)

        valid = finite_mask & valid_baseline
        detrended[valid] = lightcurve[valid] / baseline[valid]

        return detrended

    def classify_temporal_quality(self, detrended, times, transit_start, transit_end):
            pre_mask = times < transit_start
            post_mask = times > transit_end
            out_mask = pre_mask | post_mask

            pre_flux = detrended[pre_mask]
            post_flux = detrended[post_mask]
            out_flux = detrended[out_mask]

            pre_flux = pre_flux[np.isfinite(pre_flux)]
            post_flux = post_flux[np.isfinite(post_flux)]
            out_flux = out_flux[np.isfinite(out_flux)]

            if len(pre_flux) == 0 or len(post_flux) == 0 or len(out_flux) == 0:
                return {
                    "status": "rejected",
                    "oot_scatter": None,
                    "baseline_mismatch": None,
                    "reasons": ["insufficient baseline data"]
                }

            out_median = np.nanmedian(out_flux)

            mad = np.nanmedian(
                np.abs(out_flux - out_median)
            )

            oot_scatter = 1.4826 * mad

            pre_median = np.nanmedian(pre_flux)
            post_median = np.nanmedian(post_flux)

            baseline_mismatch = abs(
                pre_median - post_median
            )

            reasons = []

            if oot_scatter >= 0.002:
                reasons.append("OOT scatter >= 0.20%")

            if baseline_mismatch >= 0.0005:
                reasons.append("baseline mismatch >= 0.05%")

            if reasons:
                status = "rejected"
            elif oot_scatter >= 0.001 or baseline_mismatch >= 0.0002:
                status = "caution"

                if oot_scatter >= 0.001:
                    reasons.append("OOT scatter >= 0.10%")

                if baseline_mismatch >= 0.0002:
                    reasons.append("baseline mismatch >= 0.02%")
            else:
                status = "valid"

            return {
                "status": status,
                "oot_scatter": float(oot_scatter),
                "baseline_mismatch": float(baseline_mismatch),
                "reasons": reasons
            }

    def evaluate_dataset_quality(self, bins, times, transit_start, transit_end):
        times = np.asarray(times, dtype=float)

        pre_mask = times < transit_start
        post_mask = times > transit_end
        out_mask = pre_mask | post_mask

        scatter_values = []
        mismatch_values = []

        for bin_data in bins:
            lightcurve = bin_data.get("lightcurve")

            if lightcurve is None:
                continue

            lightcurve = np.asarray(lightcurve, dtype=float)

            detrended = self.detrend_lightcurve(
                times,
                lightcurve,
                transit_start,
                transit_end
            )

            if detrended is None:
                continue

            pre_flux = detrended[pre_mask]
            post_flux = detrended[post_mask]
            out_flux = detrended[out_mask]

            pre_flux = pre_flux[np.isfinite(pre_flux)]
            post_flux = post_flux[np.isfinite(post_flux)]
            out_flux = out_flux[np.isfinite(out_flux)]

            if len(pre_flux) == 0 or len(post_flux) == 0 or len(out_flux) == 0:
                continue

            out_median = np.nanmedian(out_flux)

            mad = np.nanmedian(
                np.abs(out_flux - out_median)
            )

            robust_scatter = 1.4826 * mad

            pre_median = np.nanmedian(pre_flux)
            post_median = np.nanmedian(post_flux)

            baseline_mismatch = abs(
                pre_median - post_median
            )

            if np.isfinite(robust_scatter):
                scatter_values.append(robust_scatter)

            if np.isfinite(baseline_mismatch):
                mismatch_values.append(baseline_mismatch)

        if len(scatter_values) == 0 or len(mismatch_values) == 0:
            return {
                "status": "poor",
                "median_oot_scatter": None,
                "median_baseline_mismatch": None,
                "bins_evaluated": 0,
                "reasons": ["insufficient temporal quality data"]
            }

        scatter_values = np.asarray(scatter_values, dtype=float)
        mismatch_values = np.asarray(mismatch_values, dtype=float)

        median_scatter = float(np.nanmedian(scatter_values))
        median_mismatch = float(np.nanmedian(mismatch_values))

        reasons = []

        if median_scatter >= 0.01:
            reasons.append("median OOT scatter >= 1.00%")

        if median_mismatch >= 0.0015:
            reasons.append("median baseline mismatch >= 0.15%")

        if reasons:
            status = "poor"
        elif median_scatter >= 0.0025 or median_mismatch >= 0.0005:
            status = "caution"

            if median_scatter >= 0.0025:
                reasons.append("median OOT scatter >= 0.25%")

            if median_mismatch >= 0.0005:
                reasons.append("median baseline mismatch >= 0.05%")
        else:
            status = "good"

        return {
            "status": status,
            "median_oot_scatter": median_scatter,
            "median_baseline_mismatch": median_mismatch,
            "bins_evaluated": len(scatter_values),
            "reasons": reasons
        }






            



            