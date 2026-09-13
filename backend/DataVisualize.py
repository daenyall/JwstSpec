import pandas as pd
import matplotlib.pyplot as plt

class DataVisualizer:

    def plot_spectrum(self,target_name, df: pd.DataFrame):
        plt.plot(df['WAVELENGTH'], df['FLUX_NORMALIZED'], color='skyblue')
        plt.title(f"{target_name} spectrum")
        plt.xlabel("WAVELENGTH")
        plt.ylabel('FLUX_NORMALIZED')
        plt.grid()
        plt.savefig("output.jpg")
        plt.show()

    def plot_lightcurves(self, target_name, df: pd.DataFrame):
        gas_columns = df.drop(columns=['MJD-AVG'])
        for gas in gas_columns:

            plt.plot(df['MJD-AVG'], df[gas], label=gas)

        plt.title(f"{target_name} - lightcurves analysis")
        plt.xlabel("MJD time")
        plt.ylabel("Normalized flux")
        plt.legend()
        plt.grid()
        plt.savefig("lightcurves_output.jpg")
        plt.show()