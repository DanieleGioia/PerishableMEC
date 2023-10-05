from policies.PolicySingleEchelon import PolicySingleEchelon
import numpy as np

class SingleEchCOP_BSP(PolicySingleEchelon):
    def __init__(self, store_setting: dict, prod_setting: dict, paramsDispatch: dict, paramsOther: dict = ...):
        super().__init__(store_setting, paramsDispatch, paramsOther)
        """
        It dispatched firectly according to I (I number of retailers) either costant or BaseStockPoliciy-based values.
        By default, all the retailers are set COP. .setBSP() and .setCOP() allow for policies mixture.

        E.g., 
        two retailers ['North', 'South'].
        paramsDispatch['North'] = 600 #BSP
        paramsDispatch['South'] = 120 #COP
        policy.setBSP('North')
        policy.setCOP('South')

        """
        self.name = 'single echelon BSP-COP'
        self.store_setting = store_setting
        #BSP and COP sets
        self.cop_ret = []
        self.bsp_ret = []
        for k in store_setting.keys():
            self.cop_ret.append(k) #all cop by default
        #
        self.paramsDispatch = paramsDispatch
        self.prod_setting = prod_setting
        self.paramsOther = paramsOther
        self.dispatched = {}
        self.dim = len(store_setting.keys())
        self.lb = np.zeros(self.dim) #lower bound on params
        #max to order (can also be s.t. constraints)
        self.ub = np.ones(self.dim)
        for i,k in enumerate(store_setting.keys()):
            self.ub[i] =  (self.store_setting[k]['ev_Daily'] + 3 * self.store_setting[k]["std_Daily"])
            self.lb[i] += 0*self.store_setting[k]['ev_Daily'] #Lower bound can be increased (within reasonable bounds)

        ############
    def decide(self, obs):
        """
        The observation format must be a dictionary where the keys are the retailer names
        E.g., 
            2 retailers (North and South)
            obs.keys() = ['North','South']
        For each key there is a dict of np.array inside with the current OnHand and OnOrder age-based items

        The decision must be made of one dict:
         -containing the dispatched with keys the retailer names
        """
        self.initDecision()
 
        #The items are considered as new as the producer can provide them
        #COP
        for k in self.cop_ret:
            for d in range(self.prod_setting['SL'] - self.prod_setting['LT'] - 1):
                self.dispatched.get(k)[d] = 0
            self.dispatched.get(k)[self.prod_setting['SL'] - self.prod_setting['LT']-1] = np.rint(self.paramsDispatch[k])
        #BSP
        for k in self.bsp_ret:
            for d in range(self.prod_setting['SL'] - self.prod_setting['LT'] - 1):
                self.dispatched.get(k)[d] = 0
            orderSize = np.max([self.paramsDispatch[k] - sum(obs[k]['inventory']) - sum(sum(obs[k]['dispatched'])),0]) #BSP
            self.dispatched.get(k)[self.prod_setting['SL'] - self.prod_setting['LT'] - 1] = np.rint(orderSize)
        ########
        return {},self.dispatched

    def xToParams(self, x:np.array):
        """
        It transforms an array input into params format
        """
        #check values
        for i in range(len(x)):
            if x[i] > self.ub[i] or x[i] < self.lb[i]:
                raise ValueError('parameters out of boundaries')
        params_disp = {}
        for i,k in enumerate(self.store_setting.keys()):
            params_disp[k] = x[i]
        return params_disp,{} #empty for other params, required for uniformity with other policies

    ####
    def setBSP(self,reatilerName: str):
        # was it COP?
        if reatilerName in self.cop_ret:
            self.bsp_ret.append(reatilerName)
            self.cop_ret.remove(reatilerName)
            #upperbound adjustment
            tmpKeyList = list(self.store_setting)
            indx = tmpKeyList.index(reatilerName) #original order
            self.ub[indx] = (self.prod_setting['SL'])*(self.store_setting[reatilerName]['ev_Daily'] + 3 * self.store_setting[reatilerName]["std_Daily"])
        #was it BSP yet?
        elif reatilerName in self.bsp_ret:
            pass
        else:
            raise ValueError('the retailer does not exist.')

    ####
    def setCOP(self,reatilerName: str):
        # was it BSP?
        if reatilerName in self.bsp_ret:
            self.cop_ret.append(reatilerName)
            self.bsp_ret.remove(reatilerName)
            #upperbound adjustment
            tmpKeyList = list(self.store_setting)
            indx = tmpKeyList.index(reatilerName) #original order
            self.ub[indx] = (self.store_setting[reatilerName]['ev_Daily'] + 3 * self.store_setting[reatilerName]["std_Daily"])
        #was it COP yet?
        elif reatilerName in self.cop_ret:
            pass
        else:
            raise ValueError('the retailer does not exist.')