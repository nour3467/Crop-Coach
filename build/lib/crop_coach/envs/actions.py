# -- Importing dependencies :
import datetime
import random
from copy import deepcopy
from typing import List
import yaml
from pprint import pprint
from typing import Union, Tuple, Dict


def return_apr_dict(
    action: str,
    irrigation_amount: Union[int, float],
    N_amount: Union[int, float],
    P_amount: Union[int, float],
    K_amount: Union[int, float],
) -> Tuple[dict, dict]:
    """This function generates action dict, in pcse format, for the given action and amount

    ---------------------------------------------------------------------
    :param action : given agriculture action (eg. "irrigate" or "fertilize")
    :type action : str
    :param irrigation_amount : irrigation amount
    :type irrigation_amount : Union[int, float]
    :param N_amount : Nitrogen amount
    :type N_amount : Union[int, float]
    :param P_amount : Phosphorus amount
    :type P_amount : Union[int, float]
    :param K_amount : Potassium amount
    :type K_amount : Union[int, float]

    ---------------------------------------------------------------------
    :return a : the action description
    :rtype a : dict
    :return b : the action event
    :rtype b : dict
    """

    a, b = None, None
    if action == "irrigate":
        a = {
            "event_signal": "irrigate",
            "name": "Irrigation application table",
            "comment": "All irrigation amounts in cm",
        }
        b = {"amount": irrigation_amount, "efficiency": 0.7}
    if action == "fertilize":
        a = {
            "event_signal": "apply_npk",
            "name": "Timed N/P/K application table",
            "comment": "All fertilizer amounts in kg/ha",
        }
        b = {
            "N_amount": N_amount,
            "P_amount": P_amount,
            "K_amount": K_amount,
            "N_recovery": 0.7,
            "P_recovery": 0.7,
            "K_recovery": 0.7,
        }
    return a, b


def generate_action_dict(
    action: str,
    periodicity: int,
    std: datetime.datetime,
    tot_days: int,
    seed: int,
    irrigation_amount: Union[int, float],
    N_amount: Union[int, float],
    P_amount: Union[int, float],
    K_amount: Union[int, float],
    cost: Union[int, float] = 0,
) -> Tuple[dict, Union[int, float]]:
    """This function generates the action full dict with events_table, event_signal and comment name

    ---------------------------------------------------------------------
    :param action :  the action itself (eg. "irrigate" or "fertilize")
    :type action : str
    :param periodicity : how much days the action will  apply periodically (eg. if periodicity = 15, the action will apply every 15 days)
    :param std : the starting date of the process
    :type std : datetime.datetime
    :param tot_days : total number of days
    :type tot_days : int
    :param seed : facilitate reproduction
    :type seed : int
    :param cost : the action cost (default : 0)
    :type cost : Union[int, float]

    ---------------------------------------------------------------------
    :return dicton : wofost formatted action dict
    :rtype dicton : dict
    :return tot_cost : the total cost of the actions
    :rtype tot_cost : Union[int, float]
    """

    random.seed(seed)
    dicton, b = return_apr_dict(action, irrigation_amount, N_amount, P_amount, K_amount)
    i = 0
    flag = 0
    tot_cost = 0
    while i <= tot_days:
        if periodicity > 0 and i % periodicity == 0:
            if "events_table" not in dicton:
                dicton["events_table"] = []
            dicton["events_table"].append({std + datetime.timedelta(i): b})
            flag = 1
            tot_cost += cost
        i += 1
    if flag == 1:
        return dicton, tot_cost
    else:
        return None, tot_cost


def gen_agromanager(
    base: List[dict],
    dicton: dict,
    costs: dict,
    irrigation_amount: Union[float, int],
    N_amount: Union[float, int],
    P_amount: Union[float, int],
    K_amount: Union[float, int],
    seed: int = 5676,
) -> Tuple[dict, Union[float, int]]:
    """This function simply generates an agromanager

    ---------------------------------------------------------------------
    :param base : agro yaml configuration file
    :type base : List[dict]
    :param dicton :  periodicity dict  (eg. {'fertilize': 15, 'irrigate': 1})
    :type dicton : dict
    :param dict_costs : costs of actions  (eg. {'fertilize': 0, 'irrigate': 0})
    :type dict_costs : dict
    :param seed : facilitate reproduction
    :type seed : int

    ---------------------------------------------------------------------
    :return tot_costs : the total cost of the actions
    :rtype: tot_costs : Union[int, float]
    :return aux : agro_mangaer infos and actions
    :rtype aux : dict
    """

    aux = deepcopy(base)
    if len(aux) > 1 or len(aux[0]) > 1:
        raise ValueError("base should be a list of one element")
    sd = list(aux[0].keys())[0]
    aux[0][sd]["TimedEvents"] = []
    tot_days = (aux[0][sd]["CropCalendar"]["crop_end_date"] - sd).days
    total_cost = 0
    for action, periodicity in dicton.items():
        res, tot_cost_action = generate_action_dict(
            action,
            periodicity,
            sd,
            tot_days,
            seed,
            irrigation_amount,
            N_amount,
            P_amount,
            K_amount,
            cost=costs[action],
        )
        total_cost += tot_cost_action
        if res is not None:
            aux[0][sd]["TimedEvents"].append(res)
    return aux, total_cost


class AgroActions:
    """
    AgroActions class manages all related to agromanagement and actions
    """

    def __init__(self):
        self.actions = None

    def create_actions(
        self,
        periods_irrigation: List[int],
        periods_fertilization: List[int],
        irrigation_amount: Union[float, int],
        N_amount: Union[float, int],
        P_amount: Union[float, int],
        K_amount: Union[float, int],
        year: int,
        Agromanager_dict: dict
    ) -> Tuple[List[dict], List[Union[float, int]]]:
        """
        gen_agromanager simply generates an agromanager

        ---------------------------------------------------------------------
        :param periods_irrigation : Irrigation frequencies (eg. [0, 1, 4, 7])
        :type periods_irrigation : List[int]
        :param periods_fertilization : Fertilization frequencies (eg. [0, 15])
        :type periods_fertilization : List[int]
        :param year : the correspondent year 2017
        :type year : int

        ---------------------------------------------------------------------
        :return actions : list of actions templates (dicts)
        :rtype actions : List[dict]
        :return costs : list of costs of actions
        :rtype costs : List[Union[int, float]]
        """

        self.actions = []
        self.costs = []
        for p in periods_irrigation:
            for f in periods_fertilization:
                agro, cost = self.generate_agromanagement(
                    {"irrigate": p, "fertilize": f},
                    irrigation_amount=irrigation_amount,
                    N_amount=N_amount,
                    P_amount=P_amount,
                    K_amount=K_amount,
                    year=year,
                    Agromanager_dict=Agromanager_dict,
                )
                self.actions.append(agro)
                self.costs.append(cost)
        return self.actions, self.costs

    def generate_agromanagement(
        self,
        dict_periodicity: Dict[str, int],
        irrigation_amount: Union[float, int],
        N_amount: Union[float, int],
        P_amount: Union[float, int],
        K_amount: Union[float, int],
        year: int,
        Agromanager_dict: dict,
    ):
        """This function creates an agromanager

        ---------------------------------------------------------------------
        :param dict_periodicity : periodicity dict  (eg. {'fertilize': 15, 'irrigate': 1})
        :type dict_periodicity : dict
        :param irrigation_amount : irrigation amount
        :type irrigation_amount : Union[float, int]
        :param N_amount : N amount
        :type N_amount : Union[float, int]
        :param P_amount : P amount
        :type P_amount : Union[float, int]
        :param K_amount : K amount
        :type K_amount : Union[float, int]
        :param year : the correspondent year 2017
        :type year : int

        ---------------------------------------------------------------------
        :return agro : agromangaer infos and actions
        :rtype agro : str, in yaml format
        """
        crop_name = Agromanager_dict["crop_name"]
        variety_name = Agromanager_dict["crop_variety"]
        campaign_start_date = str(year) + Agromanager_dict["campaign_start_date"]
        crop_start_type = Agromanager_dict["crop_start_type"]
        emergence_date = str(year) + Agromanager_dict["emergence_date"]
        crop_end_type = Agromanager_dict["crop_end_type"]
        harvest_date = str(year) + Agromanager_dict["harvest_date"]
        max_duration = Agromanager_dict["max_duration"]

        agro_yaml = f"""
                - {campaign_start_date}:
                    CropCalendar:
                        crop_name: {crop_name}
                        variety_name: {variety_name}
                        crop_start_date: {emergence_date}
                        crop_start_type: {crop_start_type}
                        crop_end_date: {harvest_date}
                        crop_end_type: {crop_end_type}
                        max_duration: {max_duration}
                    TimedEvents: null
                    StateEvents: null
                """

        agromanagement = yaml.safe_load(agro_yaml)
        dict_costs = {"irrigate": 0, "fertilize": 0}  # default : {0, 0}
        agromanagement, cost_advice = gen_agromanager(
            agromanagement,
            dict_periodicity,
            dict_costs,
            irrigation_amount,
            N_amount,
            P_amount,
            K_amount,
        )

        return agromanagement, cost_advice
