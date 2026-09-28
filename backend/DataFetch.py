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

    def _filter_mission(self, object_data):
        filter_mission = object_data[
            object_data["obs_collection"] == "JWST"
        ]
        return filter_mission

    def _get_product_filename(self, object_data):
        product_filename = Observations.get_product_list(object_data)
        pd_product = product_filename.to_pandas()
        return pd_product

    def _filter_object(self, filtered_df: pd.DataFrame):
        filenames = filtered_df["productFilename"].fillna("").str.lower()

        filtered_df = filtered_df[
            filenames.str.endswith("x1dints.fits")
            & filenames.str.contains("_nis_")
            & filenames.str.contains("-seg")
        ].copy()

        if filtered_df.empty:
            raise ValueError("No segmented NIRISS/SOSS x1dints products found")

        return filtered_df

    # def _get_observation_file(self, obs_id):
    #     observation_file = Observations.download_products(obs_id)
    #     return observation_file

    def _download_product(self, product_row):
        filename = str(product_row["productFilename"])
        data_uri = str(product_row["dataURI"])

        download_dir = Path(self.base_path)
        download_dir.mkdir(parents=True, exist_ok=True)

        local_path = download_dir / filename

        if local_path.exists():
            return local_path


        status, message, url = Observations.download_file(data_uri, local_path=str(local_path), cache=True)

        if status != "COMPLETE":
            raise RuntimeError(f"Failed to download {filename}: {message}")

        return local_path

    def _get_segment_number(self, filename: str) -> int:
        segment_part = filename.partition("-seg")[2]
        segment_number = segment_part[:3]

        return int(segment_number)
    def get_data(self, target_name: str) -> pd.DataFrame:
        step0 = self._search_object(target_name)
        step1 = self._filter_mission(step0)
        soss_observations = self._filter_niriss_soss(step1)

        step2 = self._get_product_filename(soss_observations)
        step3 = self._filter_object(step2)

        first_filename = step3.iloc[0]["productFilename"]
        exposure_prefix = first_filename.split("-seg")[0]

        selected_products = step3[
            step3["productFilename"].str.startswith(exposure_prefix)
        ].copy()

        selected_products["segment_number"] = selected_products[
            "productFilename"
        ].apply(self._get_segment_number)

        selected_products = selected_products.sort_values("segment_number")

        print(
            selected_products[
                ["productFilename", "segment_number"]
            ].to_string(index=False)
        )

        dataframes = []

        for _, row in selected_products.iterrows():
            product_filename = row["productFilename"]

            local_path = self._download_product(row)

            print(f"Reading {product_filename}")

            table = Table.read(local_path, hdu="EXTRACT1D")
            dataframe = table.to_pandas()

            dataframes.append(dataframe)

        if not dataframes:
            raise ValueError("No NIRISS/SOSS data could be loaded")

        fits_data = pd.concat(dataframes, ignore_index=True)

        if "TDB-MID" in fits_data.columns:
            fits_data = fits_data.sort_values("TDB-MID").reset_index(drop=True)

        print(f"Combined integrations: {len(fits_data)}")

        return fits_data
    def _filter_niriss_soss(self, object_data):
        required_columns = ["instrument_name"]

        for column in required_columns:
            if column not in object_data.colnames:
                raise ValueError(f"MAST observation table does not contain '{column}'")

        mask = []

        for row in object_data:
            instrument = str(row["instrument_name"]).upper()
            filters = str(row["filters"]).upper() if "filters" in object_data.colnames else ""

            is_niriss = "NIRISS" in instrument
            is_soss = "GR700XD" in instrument or "GR700XD" in filters

            mask.append(is_niriss and is_soss)

        filtered = object_data[mask]

        if len(filtered) == 0:
            raise ValueError("No JWST NIRISS/SOSS observations found for this target")

        print(f"Found {len(filtered)} NIRISS/SOSS observations")

        return filtered