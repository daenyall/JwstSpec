import pandas as pd
import numpy as np
class DataPreprocessor():

    def preprocess(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        df = raw_df[['WAVELENGTH', 'FLUX']].copy()
        df['FLUX_NORMALIZED'] = df['FLUX'] / df['FLUX'].median()
        return df

    def extract_lightcurve(self, raw_table, target_wave: float):
       waves = np.array(raw_table['WAVELENGTH'][0])
       if(target_wave >= min(waves) and target_wave <= max(waves)):
            difference = np.absolute(waves - target_wave)
            index = difference.argmin()
            flux_matrix = np.vstack(raw_table['FLUX'])
            wave_flux = flux_matrix[:, index]
            wave_flux = wave_flux.astype(float)
            normalized_wave_flux = wave_flux / np.nanmedian(wave_flux)
            return normalized_wave_flux
       else:
           print(f"Warning: wave {target_wave} out of the instrument's range")
           return None

    def extract_all_gases(self, raw_table, gases_dict):
        results = {}
        for gas_name, wave in gases_dict.items():
            extracted_curve = self.extract_lightcurve(raw_table, wave)
            if(extracted_curve is not None):
                results[gas_name] = extracted_curve
        df_results = pd.DataFrame(results)
        return df_results


