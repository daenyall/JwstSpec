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

        for gas in df.columns:

            plt.plot(df.index, df[gas], label=gas)

        plt.title(f"{target_name} - lightcurves analysis")
        plt.xlabel("Time")
        plt.ylabel("Normalized flux")
        plt.legend()
        plt.grid()
        plt.savefig("lightcurves_output.jpg")
        plt.show()