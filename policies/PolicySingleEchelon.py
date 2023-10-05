import abc
from abc import abstractmethod
import numpy as np

class PolicySingleEchelon(object):
    """Base class for SingleEchelon perishable inventory systems policies"""
    __metaclass__ = abc.ABCMeta
    @abstractmethod
    def __init__(self, store_setting:dict, prod_setting: dict, paramsDispatch:dict, paramsOther: dict = {}):
        """
        One dictionary with parameters for dispatches is expected. 
        If more complext policies (VFA, DeepL, exc) need other parameters, paramsOther may fit the purpose.
        the initialization also requires the setting of the retailers.

        NOTE: if no parameters are provided, please pass the dictionary with the right keys, but with empty values.
         e.g.,
        paramsDispatch['North'] = []
        paramsDispatch['South'] = []
        """
        self.name = None
        self.store_setting = store_setting
        self.prod_setting = prod_setting
        self.paramsDispatch = paramsDispatch
        self.paramsOther = paramsOther
        self.dispatched = {}
        self.dim = 0 #overall parameter dimension
        
    @abstractmethod
    def decide(self, obs):
        """
        The observation format must be a dictionary where the keys are the retailer names.
        E.g., 
            2 retailers (North and South)
            obs.keys() = ['North','South']
        For each key there is a dict of np.array inside with the current OnHand and OnOrder age-based items

        The decision must be made of one dict:
         -it contains the dispatched with keys the retailer names. Each value of the dict has an array with size equal to the retailer's maximum possible shelf-life.
        """
        self.initDecision()

    def initDecision(self):
        """
        Initialization of the decision dictionary/arrays
        """
        #order initialization
        for k in self.store_setting.keys():
            self.dispatched[k]= np.zeros(self.prod_setting['SL'] - self.prod_setting['LT'])

    def setParameters(self,paramsDispatch:dict, paramsOther: dict = {}):
        """
        Parameters setter
        """
        self.paramsDispatch = paramsDispatch
        self.paramsOther = paramsOther
    
    @abstractmethod
    def xToParams(self, x:np.array):
        """
        It transforms an array input into params format
        """
