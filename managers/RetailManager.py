import numpy as np

class RetailManager():
    """
    """
    def __init__(self,name,scenarioMgr,lifo_params,invManager,supManager,timeHorizon,pricesRetail,markdownRetail,costRetailer = 0):
        self.scenarioMgr = scenarioMgr
        self.invManager = invManager
        self.supManager = supManager
        self.flagPrint = False
        self.timeHorizon = timeHorizon
        self.name = name
        self.makeScenario()
        self.prices = pricesRetail
        self.markdowns = markdownRetail
        #issuing policy
        if lifo_params['Type'] == 'LS': 
            self.simulateLIFO = lambda x: np.random.binomial(x,np.random.beta(lifo_params['params']['alpha'],lifo_params['params']['beta'],1)).item()
        elif lifo_params['Type'] == 'LF':
            self.simulateLIFO = lambda x: np.random.binomial(x,lifo_params['params']['dirac'])
        else:
            raise ValueError('Lifo setting not available')
        #step
        self.current_step = 0
        #statistics and plots
        #oreder history, useful to study the shape of the policy per product
        self.totProfit = 0
        self.lostDemand = 0
        self.totScrapped = 0
        self.totSold = 0
        self.totDispatched = 0
        #sales per product per day
        self.history = []
        #only if there is not a depot
        self.cost = costRetailer
    #
    def setFlagPrint(self,flag: bool):
        self.flagPrint = flag
    #
    def setTimeHorizon(self,timeHorizon):
        #when the time horizon is updated, the scenario is updated as well
        self.timeHorizon = timeHorizon
        self.makeScenario() 
    #
    def makeScenario(self):
        self.scenario = self.scenarioMgr.makeScenario(self.timeHorizon,self.name)
    #
    def reset(self):
        self.current_step = 0
        #clear inventories and onOrder
        self.invManager.clearState()
        self.supManager.clearState()
        self.history = []
        #observation
        obs = {}
        obs['inventory'] = np.zeros(self.invManager.ShelfLife).copy()
        obs['dispatched'] = []
        #We initialize the dispatched value stacking up array with length the maximum shelf life. This is due to the possibility of having different suppliers with different
        #maximum shelf life (and perhaps differnt costs and lead time). Such variation has not yet been investigated. 
        for i in range(self.supManager.LeadTime):
            if i != 0:
                obs['dispatched'] = np.row_stack((obs['dispatched'], np.zeros(self.invManager.ShelfLife).copy()))
            else:
                obs['dispatched'] = np.zeros(self.invManager.ShelfLife).copy()

        #clear statistics
        self.totProfit = 0
        self.lostDemand = 0
        self.totScrapped = 0
        self.totSold = 0
        self.totDispatched = 0
        self.makeScenario() #update scenario
        #
        return obs,0,0,0,0
    #
    def step(self,orderSize: np.array):
        #simulation of one day
        #new step
        self.current_step += 1
        #Shipped items from the depot at the end of the day
        self.supManager.GetOrder(orderSize)
        self.history.append(orderSize)
        #Debug prints
        if self.flagPrint: 
            #current inventory
            print('------------------------------------------')
            print('RETAILER: ',self.name)
            print('\nDay',self.current_step,'\nInventory:')
            #product insight
            print('Product Stored')
            for i in range(self.invManager.ShelfLife-1):
                print('\t', self.invManager.Inventory[i],'items with ', i+1, 'Residual shelf life')
            #current on order
            print(' shipped by depot to retailer ', self.name, ':')
            #Depot actions on this retailer
            print('Waiting for: ')
            for i in range(self.supManager.LeadTime+1):
                if i != 0:
                    print('\t',np.rint(self.supManager.OnOrder[i]),' items, expected in', i, 'days')
                else:
                    print('\t',np.rint(self.supManager.OnOrder[i]),' items have just arrived.')
            #total demand
            print('Demand: ', self.scenario[0][self.current_step])
        #####
        #The store opens
        #####
        #we receive the items
        delivered = self.supManager.deliverSupply()
        self.invManager.receiveSupply(delivered)
        #we sell them
        LifoC = int(self.simulateLIFO(np.rint(self.scenario[0][self.current_step]))) #number of LIFO clients
        FifoC = int(np.rint(self.scenario[0][self.current_step]) - LifoC) #number of FIFO clients
        if self.flagPrint: 
            print("Lifo = ",LifoC," Fifo = ",FifoC)
        #First lifo then fifo, but since there are no price differences, it has no effect on the retailer proift or number of stockouts.
        LifoSold = self.invManager.meetDemandLifo(LifoC)
        FifoSold = self.invManager.meetDemandFifo(FifoC)
        if self.flagPrint: 
            print("Sold Lifo = ",LifoSold," Sold Fifo = ",FifoSold)
        lostClients = LifoC +  FifoC - LifoSold - FifoSold #Clients that found no items to buy
        salesSums = LifoSold + FifoSold
        #####
        #The store closes
        #####
        scrapped = 0
        scrapped = self.invManager.updateInventory()
        #Update lost demand
        self.lostDemand += lostClients
        self.totDispatched += np.sum(orderSize)
        self.totScrapped += scrapped
        profit = 0 #profit with no costs included, that is computed by the depot that knows the cost.
        #The Profit uses disaggregated sales instead (if discount policies applied)
        profit += self.prices*salesSums + self.markdowns*scrapped
        self.totSold += salesSums
        self.totProfit += profit
        #Debug prints
        if self.flagPrint:
            print(' Dispatched/Ordered(if no depot) product: ',orderSize,' Sold:  ',salesSums,' Scrapped: ',scrapped)
            print('No purchase: ',lostClients)
            print( 'Total dispatched by the depot/orederd by retailer so far ', self.totDispatched)
            print( 'Total scrapped so far', self.totScrapped)
            print( 'Total sold so far', self.totSold)
            print( 'Profit of the day ', profit)
            print('------------------------------------------')
        #### it returns the current inventory after scrapping
        #### the profit of the day
        #observation
        obs = {}
        obs['inventory'] = self.invManager.Inventory.copy()
        obs['dispatched'] = []
        for i in range(self.supManager.LeadTime):
            if i != 0:
                obs['dispatched'] = np.row_stack((obs['dispatched'], self.supManager.OnOrder[i].copy()))
            else:
                obs['dispatched'] = self.supManager.OnOrder[i].copy()

        #### 
        return obs,profit,scrapped,salesSums,lostClients

    #####
    def computeCost(self,orderSize: np.array):
        #compute costs when there is no a depot
        if self.cost == 0:
            raise ValueError('If a Depot dispatches the orders, the retailer cannot compute the costs.')
        dayCost = np.sum(orderSize)*self.cost
        if self.flagPrint: 
            print( 'Cost of the day retailer',self.name ,' = ', dayCost )
        return dayCost 

