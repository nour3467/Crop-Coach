# -- Importing general purpose dependencies :
import os
import csv
import warnings
from datetime import datetime
import random
from typing import List, Tuple, Dict, Union, Optional
import time
import numpy as np
from pprint import pprint
import warnings

# -- Importing PCSE dependencies :
from crop_coach.envs.pcse.fileinput import CABOFileReader # , YAMLCropDataProvider
from crop_coach.envs.pcse.db import NASAPowerWeatherDataProvider
from crop_coach.envs.pcse.base import ParameterProvider
from crop_coach.envs.pcse.engine import Engine
# from pcse.models import Wofost72_WLP_FD, Wofost72_PP

# -- Importing local dependencies :
# from gym_wofost.envs.actions import AgroActions
from crop_coach.envs.actions import AgroActions


# -- Read Cabo file :
def read_cabo_file(cabo_file_path: str) -> CABOFileReader:
    """Read the cabofile and return it as a CABOFileReader object

    ---------------------------------------------------------------------
    :param cabo_file_path: The path to the cabo file
    :type cabo_file_path: str

    ---------------------------------------------------------------------
    :return: The cabofile as a CABOFileReader object
    :rtype: CABOFileReader
    """
    return CABOFileReader(cabo_file_path)


# -- Check if the file path is valid :
def check_file_path(file_path: str) -> bool:
    """Check if the file path is valid

    ---------------------------------------------------------------------
    :param file_path: The path to the file
    :type file_path: str

    ---------------------------------------------------------------------
    :return: True if the file path is valid, False otherwise
    :rtype: bool
    """
    if os.path.isfile(file_path):
        return True
    else:
        # raise ValueError("The file path is not valid, default will be used instead")
        print("The file path is not valid, default will be used instead")
        return False



# -- Wofost simulator init :
class Wofost:
    @staticmethod
    def init_wofost(crop_name, crop_variety, files_paths : dict,latitude: float = 51.97, longitude: float = 5.67, **kwargs):
        """Init wofost simulator, by loading the crop,soil and site parameters, also initializing the weather data provider

        ---------------------------------------------------------------------
        :param latitude: latitude of the site(range from -90 to 90)
        :type latitude: int
        :param longitude: longitude of the site(range from -180 to 180)
        :type longitude: int

        ---------------------------------------------------------------------
        :return params : crop,soil and site parameters
        :rtype params : pcse.base.ParameterProvider
        """

        # -- Check if the latitude and longitude are in the correct range :
        if latitude < -90 or latitude > 90:
            warnings.warn(
                "The latitude is not in the correct range, it should be between -90 and 90, the default value is used instead"
            )
        else:
            latitude = latitude
        if longitude < -180 or longitude > 180:
            warnings.warn(
                "The longitude is not in the correct range, it should be between -180 and 180, the default value is used instead"
            )
        else:
            longitude = longitude

        # -- Check if paths provided are valid :
        cabo_files = ["soil", "site", "crop"]
        data_ = {}
        if files_paths == None:
            for file in cabo_files:
                data_[file] = read_cabo_file(os.path.join(os.path.dirname(__file__),"..","default_data", file+".cab"))
        else:
            for file in cabo_files:
                if check_file_path(files_paths[file]) :
                    # print(f"\n---------------------- files read succ : {files_paths[file]}----------------------\n")
                    data_[file] = read_cabo_file(files_paths[file])
                else :
                    data_[file] = read_cabo_file(os.path.join(os.path.dirname(__file__),"..","default_data", file+".cab"))


        # # cropd = YAMLCropDataProvider()
        # cropd = YAMLCropDataProvider(repository="https://raw.githubusercontent.com/ajwdewit/WOFOST_crop_parameters/master/")
        # cropd.set_active_crop(crop_name, crop_variety)

        # -- Init the ParameterProvider : with crop, soil and site parameters
        params = ParameterProvider(data_["crop"], data_["soil"], data_["site"])

        # -- Init the weather data provider :
        wdp = NASAPowerWeatherDataProvider(latitude, longitude)


        config = os.path.join(os.path.dirname(__file__), "..","default_data", "WLP_NPK.conf")

        # print(f"--------------------- config path : {config} --------------------")

        return params, wdp, config

    @staticmethod
    def run_wofost(agromanagement, params, wdp, config) -> Tuple[np.array, float]:
        """Run wofost simulator, for a given agromanagement (growing season)

        ---------------------------------------------------------------------
        :param agromanagement : contains the actions template withing wofost format
        :param params : contains the crop,soil and site parameters
        :param wdp : weather data provider
        :param config : wofost configuration file

        ---------------------------------------------------------------------
        :return obs : the observations ndarray
        :return yield : the correspond (yield)
        """
        # -- Init wofost engine : with the given parameters
        # wofost = Wofost72_WLP_FD(params, wdp, agromanagement)
        # config
        wofost = Engine(params, wdp, agromanagement, config)
        # -- Run wofost engine : for the given agromanagement, for growing season
        wofost.run_till_terminate()
        # -- Get the observations : from the wofost engine, summary of the growing season simulation
        # r_1 = wofost.get_summary_output()
        # r_2 = wofost.get_output()
        r = wofost.get_output()
        # -- Removing variables that are not needed : (neither none or dates)
        # print(f"\n----------- summary_output {r_1} ---------------\n")
        # print(f"\n----------- last output {r[-1]} ---------------\n")
        # for var_ in ["DOS", "DOE", "DOA", "DOM", "DOH", "DOV"]:
        #     del r[0][var_]
        # Remove all none values from r[-1] and replace them with 0
        r[-1] = {k: 0 if v is None else v for k, v in r[-1].items()}
        # remove the first element from r[-1] :
        del r[-1]['day']

        return (
            # -- Converting the dict to ndarray : (to be used as observations)
            np.array(list(r[-1].values())),
            # -- Yield is the last variable in the observations array :
            r[-1]["TWSO"],
        )
