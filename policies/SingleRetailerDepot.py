from policies.PolicyMultiEchelon import PolicyMultiEchelon
import numpy as np

class SingleRetailerDepotPolicy(PolicyMultiEchelon):
    def __init__(self, store_setting:dict, prod_setting: dict, paramsOrder: float, paramsDispatch:dict, paramsOther: dict = {}):
        """
        It decides how much to order and dispatches the residual inventory after the depot demand has been fulfilled to 
        ONE SINGLE additional retailer.

        It is possible to set either COP or BSP policies for orders and for dispatch requests as well. These last will be subject to the inventory availablity
        and they will be sent according to a either a LIFO or a FIFO internal issuing policy. 

        By default, the policy ats as a full pull policy, COP on orders, COP on dispatch
        according to a internal FIFO issuing policy

        E.g., COP orders COP disp
        paramsOrder[] = [230] #COP order
        paramsDispatch['OffLine'] = 150 #COP to dispatch IF available

        """
        self.name = "Single Retailer Depot Policy"
        self.SL = prod_setting['SL'] - prod_setting['LT']
        self.store_setting = store_setting
        self.offLine_setting = {key: store_setting[key] for key in store_setting.keys() if str('OnLine').find(key)}
        self.prod_setting = prod_setting
        self.paramsOrder = paramsOrder
        self.paramsDispatch = paramsDispatch
        self.paramsOther = paramsOther
        self.orderPolicy = 'COP'
        self.dispatchPolicy = 'COP'
        self.issuingPolicy = 'FIFO'
        #2k adjustment
        self.twoKdispatch = False
        #critical adjustment
        self.criticalToServe = False
        #initializations
        self.orderSize = []
        self.dispatched = {}
        self.dim = 1 + len(self.offLine_setting.keys()) #order + dispatch
        self.lb = np.zeros(self.dim) #lower bound on params
        self.ub = np.zeros(self.dim)
        #max to order
        #COP based, changes if the user set BSP
        #max to order for retailers
        for i,k in enumerate(self.offLine_setting.keys()):
            self.ub[1+i] = (self.store_setting[k]['ev_Daily'] + 3 * self.store_setting[k]["std_Daily"])
            self.lb[1+i] = 0*self.store_setting[k]['ev_Daily'] #Lower bound can be increased (within reasonable bounds)
        for k in store_setting.keys():
            self.ub[0] += (self.store_setting[k]['ev_Daily'] + 3 * self.store_setting[k]["std_Daily"])
            self.lb[0] += 0*self.store_setting[k]['ev_Daily'] #Lower bound can be increased (within reasonable bounds)
    
    #allows for selecting a BSP or COP order policy
    def setOrderPolicy(self,orderPolicy: str):
        if self.orderPolicy == orderPolicy:
            return
        if orderPolicy == 'COP':
            self.ub[0] = 0 
            self.orderPolicy = orderPolicy
            for k in self.store_setting.keys():
                self.ub[0] += (self.store_setting[k]['ev_Daily'] + 3 * self.store_setting[k]["std_Daily"])
        elif orderPolicy == 'BSP':
            self.ub[0] = 0 
            self.orderPolicy = orderPolicy
            for k in self.store_setting.keys():
                #SL at deposit
                self.ub[0] += (self.prod_setting['SL'] - 1)* (self.store_setting[k]['ev_Daily'] + 3 * self.store_setting[k]["std_Daily"])            
        else:
            raise ValueError('Order policy not available')

    #allows for selecting a BSP or COP dispatch policy
    def setDispatchPolicy(self,dispatchPolicy: str):
        if self.dispatchPolicy == dispatchPolicy:
            return
        if dispatchPolicy == 'COP':
            self.dispatchPolicy = dispatchPolicy
            for i,k in enumerate(self.offLine_setting.keys()):
                self.ub[i+1] = (self.store_setting[k]['ev_Daily'] + 3 * self.store_setting[k]["std_Daily"])
        elif dispatchPolicy == 'BSP':
            self.dispatchPolicy = dispatchPolicy
            for i,k in enumerate(self.offLine_setting.keys()):
                #SL at deposit - LT - 1 to deposit +RLT
                self.ub[i+1] = (self.prod_setting['SL'] - self.prod_setting['LT'] - 1 + self.store_setting[k]['RLT'] )* (self.store_setting[k]['ev_Daily'] + 3 * self.store_setting[k]["std_Daily"])            
        else:
            raise ValueError('Dispatch Policy not available')
    
    #mainting a certain amount online
    def setCriticalOnline(self):
        self.criticalToServe = True
        self.dim += 1 #new value to opt. 
        self.ub = np.concatenate([self.ub,[self.store_setting['OnLine']['ev_Daily']]]) #Upper bound can be increased/decreased (within reasonable bounds)
        self.lb = np.concatenate([self.lb,[0]]) #Lower bound can be increased (within reasonable bounds)
    
    def set2k(self):
        if self.dispatchPolicy == 'BSP':
            self.twoKdispatch = True
            # k, w_old, w_new
            for k in self.offLine_setting.keys():
                self.dim += 3 #new value to opt. 
                rlt = self.store_setting.get(k)['RLT']
                self.ub = np.concatenate([self.ub,[self.SL - rlt - 1,1,1]])
                self.lb = np.concatenate([self.lb,[0,0,0]]) 
        else:
            raise ValueError('You can set EW adjustment only for BSP.')

    #set internal policy to dispatch 
    def setInnerIssuing(self,issuingPolicy:str ):
        if self.issuingPolicy == issuingPolicy:
            return
        if issuingPolicy == 'LIFO' or 'FIFO':
            self.issuingPolicy = issuingPolicy
        else:
            raise ValueError('Issuing Policy not available')

    ############
    def decide(self, obs):
        #
        self.initDecision()
        #Orders
        if self.orderPolicy == 'COP':
        #It orders in a constant way the freshest possible
            self.orderSize[self.SL-1] = np.rint(self.paramsOrder) 
        if self.orderPolicy == 'BSP':
            #BSP tmp var
            sumRetsInv = 0
            sumRetsOnO = 0
            for l in self.offLine_setting.keys(): 
                sumRetsInv += sum(obs[l]['inventory'])
                sumRetsOnO += np.sum(obs[l]['dispatched'])
            self.orderSize[self.SL-1]  = np.rint(np.max([(self.paramsOrder - sumRetsInv - sumRetsOnO - sum(obs['Depot']['inventory']) - np.sum(obs['Depot']['ordered'])),0]))
        #Dispatch
        retailer_req = {}
        for i,k in enumerate(self.paramsDispatch.keys()):
            if self.dispatchPolicy == 'BSP':
                if self.twoKdispatch:
                    retailer_req[k] = np.rint(np.max([self.paramsDispatch[k] - np.sum((obs[k]['dispatched'])) - self.paramsOther[3*i+1]*np.sum(obs[k]['inventory'][:int(self.paramsOther[3*i])]) - self.paramsOther[3*i+2]*np.sum(obs[k]['inventory'][int(self.paramsOther[3*i]):]),0])) #BSP2k
                else:
                    retailer_req[k] = np.max([self.paramsDispatch[k] - sum(obs[k]['inventory']) - np.sum((obs[k]['dispatched'])),0]) #BSP
            else:
                retailer_req[k] = self.paramsDispatch[k]
        #Now the depot decides what can serve
        if obs['Depot']['ordered'].ndim > 1:
            availableInv = obs['Depot']['inventory'].copy() + obs['Depot']['ordered'][0].copy()
        else: #LT = 1 
            availableInv = obs['Depot']['inventory'].copy() + obs['Depot']['ordered'].copy()
        ## if we have a quantity to maintain in the online
        if self.criticalToServe:
            criticalToServe = self.paramsOther[-1]
            if self.issuingPolicy == 'FIFO': #it reteins LIFO
                list_ages_r =  reversed(range(self.SL))
            else: #it reteins FIFO
                list_ages_r = range(self.SL)
            for d in list_ages_r:
                if  criticalToServe > 0:
                    disp = np.min([criticalToServe,availableInv[d]]) #reserved of this age
                    availableInv[d] -= disp
                    criticalToServe -= disp #update queue
        #####
        for k in self.offLine_setting.keys(): #backward priority
            queue = np.rint(retailer_req[k]) #initialization of what the retailer wants
            if self.issuingPolicy == 'FIFO':
                list_ages = range(self.SL - self.store_setting.get(k)['RLT'])
            else:
                list_ages = reversed(range(self.SL - self.store_setting.get(k)['RLT']))                
            for d in list_ages: # no expired items are sent
                if queue > 0: #still not fulfilled?
                    disp = np.min([queue,availableInv[d + self.store_setting.get(k)['RLT']]]) #dispatched of this age
                    self.dispatched.get(k)[d] = int( np.rint(disp)) #dispatched
                    availableInv[d + self.store_setting.get(k)['RLT']] -= disp
                    queue -= disp #update queue
        ########
        return self.orderSize,self.dispatched

    def xToParams(self, x:np.array):
        """
        It transforms an array input into params format
        """
        #check on params
        for i in range(len(x)):
            if x[i] > self.ub[i] or x[i] < self.lb[i]:
                raise ValueError('parameters out of boundaries')
        params_ord = x[0]
        params_disp = {}
        for i,k in enumerate(self.offLine_setting.keys()):
            params_disp[k] = x[i + 1]
        if len(x)> 1+len(self.offLine_setting.keys()):
            params_oth = x[1+len(self.offLine_setting.keys()):]
        else:
            params_oth = {}
        return params_ord, params_disp, params_oth