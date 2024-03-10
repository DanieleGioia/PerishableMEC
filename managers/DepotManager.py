import numpy as np

class DepotManager():
    """
    """
    def __init__(self,invManager,supManager,deliveryTimes,cost_depot,timeHorizon,scenarioMgr = None,lifo_params: dict = {}, priceDepot: float = 0, markdownDepot: float = 0):
        self.scenarioMgr = scenarioMgr
        self.invManager = invManager
        self.supManager = supManager
        self.deliveryTimes = deliveryTimes
        self.cost_dep = cost_depot
        self.timeHorizon = timeHorizon
        self.flagPrint = False
        #Initialization of retail-oriented quantities
        self.makeScenario()
        self.prices = priceDepot
        self.markdowns = markdownDepot
        #issuing policy
        if lifo_params['Type'] == 'LS': 
            self.simulateLIFO = lambda x : np.random.binomial(x,np.random.beta(lifo_params['params']['alpha'],lifo_params['params']['beta'],1)).item()
        elif lifo_params['Type'] == 'LF':
            self.simulateLIFO = lambda x : np.random.binomial(x,lifo_params['params']['dirac'])
        else:
            raise ValueError('Lifo setting not available')
        #step
        self.current_step = 0
        #retails insight
        self.keys_ret = list(deliveryTimes.keys())
        self.nRetails = len(self.keys_ret)     
        #statistics and plots
        #oreder history, useful to study the shape of the policy per product
        self.history = []
        self.totProfit = 0
        self.lostDemand = 0
        self.totSold = 0
        self.totCost = 0
        self.totScrapped = 0
        #dispatched
        self.totDispatchedPerRet = {}
    #
    def setFlagPrint(self,flag: bool):
        self.flagPrint = flag

    def setTimeHorizon(self,timeHorizon):
        self.timeHorizon = timeHorizon
        #When we update the time horizon we need to update the scenrio accordingly
        self.makeScenario() 
    #
    def reset(self):
        self.current_step = 0
        #clear inventories and onOrder
        self.invManager.clearState()
        self.supManager.clearState()
        self.history = []
        self.totSold = 0
        self.totProfit = 0
        self.lostDemand = 0
        self.makeScenario() #update scenario
        #clear statistics
        self.totCost = 0
        self.totScrapped = 0
        #dispatched
        for k in self.keys_ret:
            self.totDispatchedPerRet[k] = np.zeros(self.invManager.ShelfLife - self.deliveryTimes[k])
        ##Observation building
        obs ={}
        #sate coherent
        #Inventory
        obs["inventory"] = np.zeros(self.invManager.ShelfLife).copy()
        #We initialize the ordered value stacking up array with length the maximum shelf life. This is due to the possibility of having different suppliers with different
        #maximum shelf life (and perhaps differnt costs and lead time). Such variation has not yet been investigated. 
        for i in range(self.supManager.LeadTime):
            if i != 0:
                obs["ordered"] = np.row_stack((obs["ordered"], np.zeros(self.invManager.ShelfLife).copy()))
            else:
                obs["ordered"] =  np.zeros(self.invManager.ShelfLife).copy()
        # returns obs,cost,scrap,profit,salesSum,lostClients
        return obs,0,0,0,0,0
    
    ##
    def makeScenario(self):
        self.scenario = self.scenarioMgr.makeScenario(self.timeHorizon,'OnLine') #as depot, it can only be the online. 
    #
    def step(self,orderSize,dispatched):
        ###new step
        self.current_step += 1
        #########
        cost = 0
        scrapped = 0
        #we order
        self.supManager.GetOrder(orderSize)
        self.history.append(orderSize)
        ### 
        #we receive the items
        delivered = self.supManager.deliverSupply()
        self.invManager.receiveSupply(delivered)
        if self.flagPrint:
            print('Day',self.current_step)
            print('\t',delivered,' items have just arrived.')
        ###  
        #payment
        cost += self.cost_dep*np.sum(orderSize)
        if self.flagPrint: 
            #current inventory
            print('\nInventory depot before dispatch:')
            #product insight
            print('Product Stored')
            for i in range(self.invManager.ShelfLife):
                print('\t', self.invManager.Inventory[i],'items with ', i+1, 'Residual shelf life')
        #we dispatch
        for k in self.keys_ret:
            for d in range(self.invManager.ShelfLife - self.deliveryTimes[k]):
                #remove form inventory what dispatched
                self.invManager.meetDemand( (self.invManager.ShelfLife - self.deliveryTimes[k]) -  1 - d, dispatched[k][d])
        #Stats update
        for k in self.keys_ret:
            self.totDispatchedPerRet[k] += dispatched[k]
        self.totCost += cost
        ##Debug prints
        if self.flagPrint: 
            print('Oredered by Depot: ',orderSize)
            for k in self.keys_ret:
                print(dispatched[k],' units of product dispatched to retailer: ', k)
                print(self.totDispatchedPerRet[k],' TOTAL of units of product dispatched to retailer: ', k)
            print( 'Total scrapped so far', self.totScrapped)
            print( 'Cost of the day ', cost)
            print( 'Total cost so far ', self.totCost)
            print('-------------DAY ',self.current_step - 1,'  ENDS -------')
            print('------------------New day Begins------------------------')
             #####
        #####Morning, the day begins
        #####
        #####
        profit = 0 #profit with no costs included
        if self.flagPrint: 
            #current inventory
            print('\n Day',self.current_step,'\n inventory depot:')
            #product insight
            print('Product Stored')
            for i in range(self.invManager.ShelfLife):
                print('\t', self.invManager.Inventory[i],'items with ', i+1, 'Residual shelf life')
            print('Demand: ', self.scenario[0][self.current_step])
        #aggregated lost and unmet of the current day
        lostClients = 0 #Clients that found no items to buy
        LifoC = int(self.simulateLIFO(np.rint(self.scenario[0][self.current_step]))) #number of LIFO clients
        FifoC = int(np.rint(self.scenario[0][self.current_step]) - LifoC) #number of FIFO clients
        #First lifo then fifo, but since there are no price differences, it has no effect on the retailer proift or number of stockouts.
        LifoSold = self.invManager.meetDemandLifo(LifoC)
        FifoSold = self.invManager.meetDemandFifo(FifoC)
        lostClients = LifoC +  FifoC - LifoSold - FifoSold #Clients that found no items to buy
        salesSums = LifoSold + FifoSold
        #####
        #The store closes
        #Update lost demand
        self.lostDemand += lostClients
        ###
        #update and scrap
        scrapped = self.invManager.updateInventory() # the ageing happens after the store is closed.
        #
        profit += self.prices*salesSums + self.markdowns*scrapped
        self.totSold += salesSums
        self.totProfit += profit
        self.totScrapped += scrapped
        if self.flagPrint:
            print('Scrapped by Depot: ',scrapped)
            print(' Depot:\nSold:  ',salesSums,' Scrapped: ',scrapped)
            print('No purchase: ',lostClients)
            print( 'Total sold so far', self.totSold)
            print( 'Profit of the day ', profit)
            print('------------Night at the Depot-------------')
    
        ##Observation building
        obs ={}
        #sate coherent
        #Inventory post demand
        obs["inventory"] = self.invManager.Inventory.copy()
        #AlreadyOrdered
        for i in range(self.supManager.LeadTime):
            if i != 0:
                obs["ordered"] = np.row_stack((obs["ordered"], self.supManager.OnOrder[i].copy()))
            else:
                obs["ordered"] = self.supManager.OnOrder[i].copy()
        # returns obs,cost,scrap,profit,salesSum,lostClients
        return obs,cost,scrapped,profit,salesSums,lostClients