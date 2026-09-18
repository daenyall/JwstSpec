from DataFetch import MastApiFetcher
from DataPreprocess import DataPreprocessor
from DataVisualize import DataVisualizer
from DataAnalyzer import DataAnalyzer
import pandas as pd


def main():
    gases = {'H2O': 1.4, 'CH4': 2.3, 'CO2': 4.3}
    target_name = "WASP-96b"

    #time in days
    mid_transit = 2459751.82468
    duration = 2.4264 / 24
    half_duration = duration / 2
    midpoint = mid_transit - 2400000.5
    transit_start = midpoint - half_duration
    transit_end = midpoint + half_duration

    fetcher = MastApiFetcher(base_path="./jwst_data")
    preprocessor = DataPreprocessor()
    visualizer = DataVisualizer()
    analyzer = DataAnalyzer()

   
    fits_data = fetcher.get_data(target_name)
    preprocessed_data = preprocessor.extract_all_gases(fits_data, gases)
    depth_data = analyzer.calculate_transit_depth(preprocessed_data, transit_start, transit_end, gases)
    print(depth_data)
    visualizer.plot_lightcurves(target_name, preprocessed_data)
    

    preprocessed_data.to_csv(f"{target_name} results.csv", index_label="Time_Frame")
if __name__ == "__main__":
    main()