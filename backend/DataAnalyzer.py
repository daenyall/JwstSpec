import pandas as pd
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

        in_transit = (times >= transit_start) & (times <= transit_end)
        out_of_transit = ~in_transit

        spectrum = []
        rng = np.random.default_rng(42)

        for bin_data in bins:
            lightcurve = np.asarray(bin_data["lightcurve"], dtype=float)

            if len(lightcurve) != len(times):
                raise ValueError("Lightcurve length does not match TDB-MID length")

            in_flux = lightcurve[in_transit]
            out_flux = lightcurve[out_of_transit]

            in_flux = in_flux[np.isfinite(in_flux)]
            out_flux = out_flux[np.isfinite(out_flux)]

            if len(in_flux) == 0 or len(out_flux) == 0:
                continue

            in_transit_median = np.nanmedian(in_flux)
            out_of_transit_median = np.nanmedian(out_flux)

            if not np.isfinite(out_of_transit_median) or out_of_transit_median == 0:
                continue

            depth = (out_of_transit_median - in_transit_median) / out_of_transit_median

            bootstrap_depths = []

            for _ in range(1000):
                in_sample = rng.choice(in_flux, size=len(in_flux), replace=True)
                out_sample = rng.choice(out_flux, size=len(out_flux), replace=True)

                in_median = np.nanmedian(in_sample)
                out_median = np.nanmedian(out_sample)

                if out_median != 0:
                    bootstrap_depth = (out_median - in_median) / out_median
                    bootstrap_depths.append(bootstrap_depth)

            uncertainty = np.nanstd(bootstrap_depths, ddof=1)

            spectrum.append({
                "bin_start": float(bin_data["bin_start"]),
                "bin_center": float(bin_data["bin_center"]),
                "bin_end": float(bin_data["bin_end"]),
                "channels": int(bin_data["channels"]),
                "in_transit_median": float(in_transit_median),
                "out_of_transit_median": float(out_of_transit_median),
                "depth": float(depth),
                "uncertainty": float(uncertainty)
            })

        return spectrum










            



            