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
        filtered_df = filtered_df[
            filtered_df["productFilename"].str.endswith(
                "x1dints.fits"
            )
        ]
        return filtered_df

    def _get_observation_file(self, obs_id):
        observation_file = Observations.download_products(obs_id)
        return observation_file

    def _get_segment_number(self, filename: str) -> int:
        segment_part = filename.partition("-seg")[2]
        segment_number = segment_part[:3]

        return int(segment_number)

    def get_data(self, target_name: str) -> pd.DataFrame:

        step0 = self._search_object(target_name)
        step1 = self._filter_mission(step0)
        step2 = self._get_product_filename(step1)
        step3 = self._filter_object(step2)

        segmented_files = step3[
            step3["productFilename"].str.contains(
                "-seg",
                na=False
            )
        ].copy()

        if segmented_files.empty:
            raise ValueError(
                f"No segmented x1dints files found for {target_name}"
            )


        first_filename = segmented_files.iloc[0][
            "productFilename"
        ]

        exposure_prefix = first_filename.partition("-seg")[0]


        exposure_files = segmented_files[
            segmented_files["productFilename"].str.startswith(
                exposure_prefix + "-seg"
            )
        ].copy()

        exposure_files["segment_number"] = exposure_files[
            "productFilename"
        ].apply(self._get_segment_number)

        exposure_files = exposure_files.sort_values(
            "segment_number"
        )

        print(
            exposure_files[
                ["productFilename", "segment_number"]
            ]
        )

        dataframes = []

        for _, row in exposure_files.iterrows():

            obs_id = row["obsID"]
            product_filename = row["productFilename"]

            manifest = self._get_observation_file(obs_id)

            downloaded_files = manifest[
                "Local Path"
            ].tolist()

            local_path = next(
                path
                for path in downloaded_files
                if str(path).endswith(product_filename)
            )

            table = Table.read(
                local_path,
                hdu="EXTRACT1D"
            )

            segment_df = table.to_pandas()

            dataframes.append(segment_df)

        fits_data = pd.concat(
            dataframes,
            ignore_index=True
        )

        if "TDB-MID" in fits_data.columns:
            fits_data = fits_data.sort_values(
                "TDB-MID"
            ).reset_index(drop=True)

        print(
            "Combined integrations:",
            len(fits_data)
        )

        return fits_data