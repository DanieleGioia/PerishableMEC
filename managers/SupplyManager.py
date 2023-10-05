"""
Orders manager according to the lead times. Each product needs its SupplyManager
"""
import numpy as np

class SupplyManager:

    
    def __init__(self,LeadTime,ShelfLife = np.nan):
        self.LeadTime = LeadTime
        self.ShelfLife = ShelfLife
        if np.isnan(self.ShelfLife):
             self.OnOrder = np.zeros(LeadTime+1) #Everything fresh
        else:
            self.OnOrder = np.zeros([LeadTime+1,ShelfLife]) #Retailers mixed ages
    #Clear queue of orders
    def clearState(self):
    #If lead time is zero, use one position as a placeholder
        if np.isnan(self.ShelfLife):
             self.OnOrder = np.zeros(self.LeadTime+1) #Depot everthing fresh
        else:
            self.OnOrder = np.zeros([self.LeadTime+1,self.ShelfLife]) #Retailers mixed ages
    #Deliver the next supply order
    def deliverSupply(self):
        Delivery = self.OnOrder[0].copy()
        #now shift up
        for k in range(self.LeadTime):
            self.OnOrder[k] = self.OnOrder[k+1].copy()
        if np.isnan(self.ShelfLife):
            self.OnOrder[-1] = 0
        else:
            self.OnOrder[-1] = np.zeros(self.ShelfLife)
        return Delivery
    # Update Inventory
    def GetOrder(self,OrderSize):
        self.OnOrder[-1] = OrderSize
        

