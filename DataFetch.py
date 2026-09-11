import pandas as pd
from abc import ABC, abstractmethod
from pathlib import Path
from astropy.table import Table
from astroquery.mast import Observations

class DataFetcher(ABC):

    @abstractmethod
    def get_data(self, target_name: str) -> pd.DataFrame:
        pass

class LocalFitsFetcher(DataFetcher):

    def __init__(self, base_path: str):
        self.base_path = base_path

    def get_data(self, target_name: str) -> pd.DataFrame:
        file_path = Path(self.base_path) / f"{target_name}.fits"
        load_fits = Table.read(file_path)
        fits_data = load_fits.to_pandas()
        return fits_data

class MastApiFetcher(DataFetcher):

    def __init__(self, base_path: str):
        self.base_path = base_path

    def _search_object(self, target_name: str):
        object_data = Observations.query_object(target_name)
        return object_data

    def _filter_mission(self, object_data       ):
        filter_mission = object_data[object_data['obs_collection'] == 'JWST']
        return filter_mission

    def _get_product_filename(self, object_data):
        product_filename = Observations.get_product_list(object_data)
        pd_product = product_filename.to_pandas()
        return pd_product

    def _filter_object(self, filtered_df: pd.DataFrame):
        filtered_df = filtered_df[filtered_df['productFilename'].str.endswith('x1dints.fits')]
        return filtered_df

    def _get_filtered_id(self, filtered_df: pd.DataFrame):
        filtered_id = filtered_df['obsID'].iloc[0]
        return filtered_id

    def _get_observation_file(self, obs_id):
        get_observation_file = Observations.download_products(obs_id)
        return get_observation_file

    def get_data(self, target_name: str) -> pd.DataFrame:
        step0 = self._search_object(target_name)
        step1 = self._filter_mission(step0)
        step2 = self._get_product_filename(step1)
        step3 = self._filter_object(step2)
        step4 = self._get_filtered_id(step3)
        step5 = self._get_observation_file(step4)

        downloaded_files = step5['Local Path'].tolist()
        local_path = next(route for route in downloaded_files if route.endswith('x1dints.fits'))
        load_fits = Table.read(local_path, hdu='EXTRACT1D')
        fits_data = load_fits.to_pandas()
        return fits_data




