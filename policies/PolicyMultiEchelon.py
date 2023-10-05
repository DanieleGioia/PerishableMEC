import abc
from abc import abstractmethod
import numpy as np

class PolicyMultiEchelon(object):
    """Base class for MultiEchelon perishable inventory systems policies"""

    __metaclass__ = abc.ABCMeta

    @abstractmethod
    def __init__(self, store_setting:dict, prod_setting: dict, paramsOrder: float, paramsDispatch:dict, paramsOther: dict = {}):
        """
        Two different dictionary with parameters are expected. Each of them refer to a particular part of the poicy. The order value is a float instead.
        If more complext policies (VFA, DeepL, exc) need other parameters, paramsOther may fit the purpose.
        the initialization also requires the setting of the retailers and producer to avoid sending expired items w.r.t. the lead times.

        NOTE: if no parameters are provided, please pass the dictionary with the right keys, but with empty values.
         e.g.,
        paramsOrder = 0
        paramsDispatch['North'] = []
        paramsDispatch['South'] = []
        """
        self.name = None
        #maximum shelf life
        self.SL = prod_setting['SL'] - prod_setting['LT']
        self.store_setting = store_setting
        self.offLine_setting = {key: store_setting[key] for key in store_setting.keys() if str('OnLine').find(key)}
        self.prod_setting = prod_setting
        self.paramsOrder = paramsOrder
        self.paramsDispatch = paramsDispatch
        self.paramsOther = paramsOther
        self.orderSize = []
        self.dispatched = {}
        self.dim = 0 #overall parameter dimension

    @abstractmethod
    def decide(self, obs):
        """
        The observation format must be a dictionary where the keys are the retailer names and the Depot.
        E.g., 
            1 Depot and 2 retailers (North and South)
            obs.keys() = ['Depot','North','South']
        For each key there is a dict of np.array inside with the current OnHand and OnOrder age-based items

        The decision must be made of two dict:
         -one for the orderSize from the producer 
         -one for the dispatched with keys the retailer names. Each value of the dict has an array with size equal to the retailer's maximum possible shelf-life.

        """
        self.initDecision()

    def initDecision(self):
        """
        Initialization of the decision dictionary/arrays
        """
        #order and dispatch initialization
        for k in self.offLine_setting.keys():
            self.dispatched[k]= np.zeros(self.SL - self.store_setting.get(k)['RLT'])
        self.orderSize = np.zeros(self.SL)

    def setParameters(self,paramsOrder: float, paramsDispatch:dict, paramsOther: dict = {}):
        """
        Parameters setter
        """
        self.paramsOrder = paramsOrder
        self.paramsDispatch = paramsDispatch
        self.paramsOther = paramsOther

    @abstractmethod
    def xToParams(self, x:np.array):
        """
        It transforms an array input into params format
        """