"""
Classes to manage statistics
"""
import numpy as np

class StatManager:
    #additional values for possible transient periods
    #in the learning phases can be set.
    Head = 0 #set by setter
    Tail = 0 #set by setter
    FirstTimeBucket = 1 #default
    LastTimeBucket = 1 #default
    
    def __init__(self,store_setting: dict, Depot = True):
        self.store_setting = store_setting
        self.ret_list = list(store_setting.keys())
        self.TotalSold = {}
        self.TotalScrapped = {}
        self.TotalProfit = {}
        self.profit = {}
        self.costs = {}
        self.totLost = {}
        self.nStockOut = {}
        for k in self.ret_list: 
            self.TotalSold[k] = 0
            self.TotalScrapped[k] = 0
            self.TotalProfit[k] = 0
            self.profit[k] = 0 #tmp
            self.totLost[k] = 0
            self.nStockOut[k] = 0
            self.costs[k] = 0
        self.TotalCost = 0
        self.TimeHorizon = 0 # to be set separately
        self.myClock = 0
        # number of steps (active ones without initial head )
        self.n = 0
        #minimum number of steps
        self.minN = 120 # 18 weeks ca.
        #Terminate the simulation
        self.eps = 0.0025 #perc
        self.window = 35 #min window as default 5 weeks
        # cashFlowHistory
        self.cashFlowHist = [] 
        self.avgProfitHist = []
        #Boolean if Depot
        self.depot = Depot

    
    def clearStatistics(self):
        self.myClock = 0
        for k in self.ret_list: 
            self.TotalSold[k] = 0
            self.TotalScrapped[k] = 0
            self.TotalProfit[k] = 0
            self.profit[k] = 0
            self.costs[k] = 0
            self.totLost[k] = 0
            self.nStockOut[k] = 0
        self.TotalScrapped['Depot'] = 0 #also the depot scraps
        self.TotalCost = 0
        self.myClock = 0
        self.n = 0
        self.avgProfitHist = []
        self.cashFlowHist = []

    #Set time horizon
    def setTimeHorizon(self, TimeHorizon):
        if TimeHorizon <= self.minN:
            raise ValueError('The horizon is too short for a meaningful simulation.')
        self.TimeHorizon = TimeHorizon
        self.FirstTimeBucket = self.Head + 1
        self.LastTimeBucket = TimeHorizon
        
    #Set transient Head and Tail to discard in computing statistics
    def setHead(self, Head):
        self.Head = Head
        self.setTimeHorizon(self.TimeHorizon)
    
    #window employed to check convergence of the average
    def setEndWindow(self,window: float):
        if window <= 0:
            raise ValueError('Window must be a positive value.')
        self.window = window
    #width of the average w.r.t. the average itself
    def setEndEps(self,eps: float):
        if eps >= 1 or eps <= 0:
            raise ValueError('Please set a valid eps between 0 and 1.')
        self.eps = eps
    
    #Update functions for time steps and daily profits

    def updateClock(self):
        if self.TimeHorizon == 0:
            raise ValueError('Please set a valid time horizon.')
        self.myClock = self.myClock + 1
    #####
    def updateStatsRetailer(self,profit,scrapped, sales, lostSales ,retailName, costs = 0):
        """
        update internal clock and check if we are still in Head or already in Tail.
        It must be called at the end of each day
        Ordered  is updated according to a daily stepsize
        Scrapped is updated according to a daily stepsize
        Sales must contain the age information. It is assumed as a np.arrays, consistently with the max possible shelf life of the product.
        cost variable can be utilized only if there is not Depot

        It must called as OnLine with the partial observation from the DEPOT (profit, scrapped, lostsales)
        """
        if (self.myClock >= self.FirstTimeBucket) and (self.myClock <= self.LastTimeBucket):
            #cumulative
            self.TotalSold[retailName] += sales
            self.TotalScrapped[retailName] += scrapped
            self.TotalProfit[retailName] += profit
            self.totLost[retailName] += lostSales
            if lostSales > 0: #stockout occurs
                self.nStockOut[retailName] +=1
            #tmpProfits
            self.profit[retailName] = profit
            if not self.depot: #there is not a depot, thus the retailers pays directly for the order
                self.costs[retailName] += costs
    #  
    def updateStatsDepot(self,costs = 0): #it must be called after UpStatsRetailer
        #if there is no depot, this updates only the overall profit and acts as a dummy method
        #however, it must be called
        if (self.myClock >= self.FirstTimeBucket) and (self.myClock <= self.LastTimeBucket):
            dayProfits = 0
            if self.depot:
                self.TotalCost += costs
            else :
                costs = 0
                for k in self.ret_list:
                    self.TotalCost += self.costs[k]
                    costs += self.costs[k]
                    self.costs[k] = 0#re-initialization of the costs tmp variable
            #re_initialize tmpProfits and sum
            for k in self.ret_list:
                dayProfits += self.profit[k]
                self.profit[k] = 0 #re-initialization of the profit tmp variable
            #compute cashFlow
            cashFlow = dayProfits - costs
            self.n +=1 #cashFlows statistics counter
            self.avgProfitHist.append(self.getAverageProfit())
            self.cashFlowHist.append(cashFlow)
            return cashFlow
        else:
            return 0 # to return a reward for the first time-bucket

    #stats getters
    def getTotalRevenue(self):
        revenue = 0
        for k in self.ret_list:
            revenue += self.TotalProfit[k]
        return revenue
    def getTotalPurchaseCost(self):
        return self.TotalCost
        
    def getStockOutProb(self,retailName):
        return self.nStockOut[retailName] / self.n

    def getNumberSteps(self):
        return self.n


    def checkIfDone(self): #is the average profit stable over the window?
        if(self.myClock >= self.minN and self.n >= self.window):
            if np.all(np.array(self.avgProfitHist[self.n - self.window:self.n])<0): #we assume that makes no sense to have a negative profit strategy
                return True 
            up = np.nanmax(self.avgProfitHist[self.n - self.window:self.n])
            low = np.nanmin(self.avgProfitHist[self.n - self.window:self.n])
            return ( (up-low) <= self.eps*np.mean(self.avgProfitHist))
        else:
            return False
    #Main performance metrics
    def getAverageProfit(self):
        return (self.getTotalRevenue() - self.getTotalPurchaseCost() ) / self.n
    def getAverageUnmetClients(self):
        totLostCum = 0
        for k in self.ret_list:
            totLostCum += self.totLost[k]
        return totLostCum/ self.n        
    def getAverageScrapped(self):
        totScrapped = 0
        for k in self.ret_list:
            totScrapped += self.TotalScrapped[k]
        return totScrapped/ self.n
        
######
#####