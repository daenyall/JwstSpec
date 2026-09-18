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










        



        