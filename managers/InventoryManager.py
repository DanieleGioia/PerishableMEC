import numpy as np


class InventoryManager:
    """
    This InventoryManager implementation deals with one single customers per step
    it manages the invetory according to the ShelfLife.
    The constructor needs the maximum shelf life
    """
    def __init__(self, ShelfLife):
        self.Inventory = np.zeros(ShelfLife)
        self.ShelfLife = ShelfLife
    # Clean up inventory
    def clearState(self):
        self.Inventory = np.zeros(self.ShelfLife)
    # Update Inventory
    def updateInventory(self):
        Scrapped = self.Inventory[0]
        for i in range(self.ShelfLife - 1):
            self.Inventory[i] = self.Inventory[i+1]
        self.Inventory[self.ShelfLife-1] = 0
        return Scrapped
    def receiveSupply(self, orderSize):
        #orderSize is either an array with dim the shelfLife (a depot dispatches)
        #or it is a sinlge number (everything arrives as fresh as possible)
        if isinstance(orderSize,np.ndarray): # dispatch per shelf life
            if orderSize.size != self.ShelfLife: #check the size
                raise ValueError('OrderSize must be equal to the allowed max shelfLife')
            else:
                for i in range(self.ShelfLife):
                    self.Inventory[i] += orderSize[i] #index is the residual shelf life, the higher the newer
        else:
            self.Inventory[self.ShelfLife-1] = np.rint(orderSize)
    #Functions that simulates the demand fulfillment of 1 single item per call
    def meetDemandLifo(self, howmany = 1):
        Sales = max(0,np.min([howmany,np.sum(self.Inventory)]))
        toSell = Sales
        for age in range(self.ShelfLife):
            disp = self.Inventory[self.ShelfLife - age - 1 ]
            self.Inventory[self.ShelfLife - age - 1 ] -= max(0,np.min([toSell,disp]))
            toSell -= max(0,np.min([toSell,disp]))
        return Sales
    
    def meetDemandFifo(self, howmany = 1):
        Sales = max(0,np.min([howmany,np.sum(self.Inventory)]))
        toSell = Sales
        for ageRev in range(self.ShelfLife):
            disp = self.Inventory[ageRev]
            self.Inventory[ageRev] -= max(0,np.min([toSell,disp]))
            toSell -= max(0,np.min([toSell,disp]))
        return Sales

    def meetDemand(self,age, howmany = 1):
        if (not self.isAvailable(howmany)) or (not self.isAvailableAge(age,howmany)):
            raise ValueError("The customer cannot buy something missing")
        else:
            Sales = howmany
            self.Inventory[self.ShelfLife - age - 1 ] -= Sales
        return Sales

    # Is this product in stock?
    def isAvailable(self, howmany = 1): 
        return sum(self.Inventory) >= howmany
    # Is this product in stock with this particular age?
    def isAvailableAge(self, age, howmany = 1):
        if age >= self.ShelfLife or age < 0: #age cannot be equals to the SL
            raise ValueError("Age out of the bounds for this product")
        return self.Inventory[self.ShelfLife - age - 1] >= howmany
    #If I ask for this product what is on the shelf?
    def getProductAvailabilty(self):
        return list(map(bool,self.Inventory.tolist()))

