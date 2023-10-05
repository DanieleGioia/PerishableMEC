import gym
import numpy as np

class DailySimulation(gym.Env):
    '''
    The observation is a dictionary that has as key the name of the store and as value
    the the current inventory divided per residual shelf life.

    The action is assumed as a np.array and a dict that refelct the number of parameter needed by the depot (decision maker)
    to order and to dispatch products.

    If there is no depot, the depot variable is set to None
    '''
    #output precision
    np.set_printoptions(precision=3)
    np.set_printoptions(suppress=True)

    def __init__(self,retailers,depot,statMgr,timeHorizon,flagPrint = False):
        super(DailySimulation,self).__init__()

        #managers of the simulation
        self.retailers = retailers
        self.depot= depot #None if there is no depot
        self.timeHorizon = timeHorizon
        self.statMgr = statMgr
        self.learn = True
        self.statMgr.setTimeHorizon(self.timeHorizon) #set time horizon
        #debug print recursively activated
        self.flagPrint = flagPrint
        if self.flagPrint:
            for k in self.retailers.keys():
                self.retailers.get(k).setFlagPrint(True)
            if self.depot != None:
                self.depot.setFlagPrint(True)
        #step
        self.current_step = 0

    def reset(self):
        self.current_step = 0
        #dictionary obs
        obs = {}
        for k in self.retailers.keys():
            self.retailers.get(k).scenarioMgr.generated = False
            obs[k],_,_,_,_ = self.retailers.get(k).reset()
        if self.depot != None:
            obs['Depot'],_,_,_,_,_ = self.depot.reset()
        #stats clear            
        self.statMgr.clearStatistics()
        return obs

    def step(self, orderSize: np.array ,dispatched: dict):
        #new step
        self.current_step += 1
        #update clock of the stats
        self.statMgr.updateClock()
        ### depot action, starts in the evening ends in the morning
        obs = {}
        if self.depot != None:    
            obs['Depot'],cost,scrappedDepot,profitDepot,soldDepot,lostDepot = self.depot.step(orderSize,dispatched)               
        #morning

        # The stores open, receive the items and the day goes on until the end of the day inventory check
        for k in self.retailers.keys():
            obs[k],profit,scrapped,sold,lost = self.retailers[k].step(dispatched[k])
            #update general stats
            if self.depot != None:
                self.statMgr.updateStatsRetailer(profit,scrapped,sold,lost,k)
            else: #if there is not a depot
                self.statMgr.updateStatsRetailer(profit,scrapped,sold,lost,k,self.retailers[k].computeCost(dispatched[k]))
        #update general stats
        if self.depot != None:
            self.statMgr.updateStatsRetailer(profitDepot,scrappedDepot,soldDepot,lostDepot,'OnLine')
            reward = self.statMgr.updateStatsDepot(cost)
        else:
            reward = self.statMgr.updateStatsDepot() #Dummy when there is no depot, it only computes the reward
        #Debug prints
        if self.flagPrint: 
            print( 'CashFlow of the day ', reward)
            print( 'State observation: ', obs)
        #done? either MaxNumber or convergence
        done = False
        if self.learn:
            done = ( (self.current_step >= self.timeHorizon - 1) or self.statMgr.checkIfDone())
        else:
            done = (self.current_step >= self.timeHorizon - 1)
        if done and self.flagPrint:
            print('Simulation metrics:\n\tAverage Profit = ',self.getAverageProfit(),'\n\tAverage Waste = ',self.getAverageScrapped(),'\n\tAverage Unmet = ', self.getAverageUnmetClients(),'\n\tNumber of simulated weeks = ', self.statMgr.n/7)
            for k in self.retailers.keys():
                print('stockout probability retailer: ',k,' = ',self.statMgr.getStockOutProb(k))
            if self.depot != None:
                print('stockout probability retailer: OnLine(Depot) = ',self.statMgr.getStockOutProb('OnLine'))
        return obs,reward,done,{}

    #set seed of the simulation
    #  NOTICE THAT: this function is currently reduntat for a 2 retailers (Online/Offline) correlated setting.
    #  as it updates multiple time the seed of a shared scenarioMgr,
    #  however it was initlially developed for different (independent) scenarioMgrs for each retailer/depot.
    #  #TODO: adapt to correlated scenario generation
    def setSeed(self,retailName: str = 'All' ,seed = None):
        if retailName == 'All':
            for k in self.retailers.keys():
                self.retailers[k].scenarioMgr.setSeed(seed)
            if self.depot != None:  
                self.depot.scenarioMgr.setSeed(seed)
        elif self.depot != None and retailName == 'OnLine':
            self.depot.scenarioMgr.setSeed(seed)
        else:
            self.retailers[retailName].scenarioMgr.setSeed(seed)
    
    #if Test, the entire horizon runs
    def setTest(self):
        self.learn = False
    def setLearn(self):
        self.learn = True

    #update the time horizon
    def updateHorizon(self,timeHorizon):
        self.timeHorizon = timeHorizon
        self.statMgr.setTimeHorizon(self.timeHorizon)
        if self.depot != None:
            self.depot.setTimeHorizon(self.timeHorizon)
        for k in self.retailers.keys():
            self.retailers[k].setTimeHorizon(self.timeHorizon)
                
    #Metrics of the simulation
    def getAverageProfit(self):
        return self.statMgr.getAverageProfit()
    def getAverageScrapped(self):
        return self.statMgr.getAverageScrapped()
    def getAverageUnmetClients(self):
        return self.statMgr.getAverageUnmetClients()
