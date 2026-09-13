from DataFetch import MastApiFetcher
from DataPreprocess import DataPreprocessor
from DataVisualize import DataVisualizer
import pandas as pd


def main():
    gases = {'H2O': 1.4, 'CH4': 2.3, 'CO2': 4.3}
    target_name = "WASP-96b"
    fetcher = MastApiFetcher(base_path="./jwst_data")
    preprocessor = DataPreprocessor()
    visualizer = DataVisualizer()

   
    fits_data = fetcher.get_data(target_name)
    preprocessed_data = preprocessor.extract_all_gases(fits_data, gases)
    visualizer.plot_lightcurves(target_name, preprocessed_data)
    for gas in preprocessed_data.columns:
        minimum = preprocessed_data[gas].min()
        depth = (1.0 - minimum) * 100
        print(f"transit {gas}: {depth:.2f}%")
    preprocessed_data.to_csv(f"{target_name} results.csv", index_label="Time_Frame")
if __name__ == "__main__":
    main()