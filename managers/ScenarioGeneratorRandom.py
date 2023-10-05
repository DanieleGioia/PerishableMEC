import numpy as np
from scipy import stats

class ScenarioGenerationCorr:
    """
    This class generates a correlated scenario with negative binomial demand for exactly 2 distribution (Online and Offline).
    It uses a multivariate gaussian copula to generate the correlation by means of a linear correlation coefficient
    TODO: a next step concerns a further generalization of the distribution kind and a greater number of retailers
    """
    def __init__(self, distOn, muOn, sigmaOn, distOff, muOff, sigmaOff, cor):
        #Marginal distributions
        #Online retailer
        self.distOn = distOn
        self.distOff = distOff
        #Online retailer
        if self.distOn == 'Normal':
            self.On = stats.norm(muOn,sigmaOn)
        elif self.distOn == 'NB':
            self.pOn = muOn/(sigmaOn**2)
            self.nOn = (muOn*self.pOn)/((1 - self.pOn))
            self.On = stats.nbinom(self.nOn,self.pOn)
        else:
            raise ValueError('Distribution type not found')
        #Offline retailer
        if self.distOff == 'Normal':
            self.Off = stats.norm(muOff,sigmaOff)
        elif self.distOff == 'NB':
            self.pOff = muOff/(sigmaOff**2)
            self.nOff = (muOff*self.pOff)/((1 - self.pOff))
            self.Off = stats.nbinom(self.nOff,self.pOff)
        else:
            raise ValueError('Distribution type not found')        
        #seed
        self.seed = None
        #when the scenario generator generates a sample this becomes True. Use reset to make it False
        self.generated = False
        #mvr multivariate gaussian copula component
        self.mvnorm = stats.multivariate_normal(mean=[0,0], cov=[[1., cor], [cor, 1.]])

    def setSeed(self,seed):
        self.seed = seed
        
    #Fixed seed reset
    def reset(self, timeHorizon = None):
        np.random.seed(self.seed)
        self.generated = True
        #if no time horizon specified, use the one we saved in last makeScenario call. 
        if timeHorizon == None:
            timeHorizon = self.timeHorizon
        #rmnvnorm
        copula = stats.norm.cdf(self.mvnorm.rvs(timeHorizon))
        #pre-allocation
        #pre-allocation
        self.demandScenarioOff = np.zeros( (1, timeHorizon) )
        self.demandScenarioOn = np.zeros( (1, timeHorizon) )

        self.demandScenarioOn[0] = self.On.ppf(copula[:,0])
        self.demandScenarioOff[0] = self.Off.ppf(copula[:,1])
    
    def makeScenario(self, timeHorizon, ret):
        """
        Retailer either Off or On. It generates a new scenario only when resetted. Oth it only access them.
        """
        #check weekly pattern
        self.checkTimeHorizon(timeHorizon) 
        #is the scenario generated yet?
        if not self.generated:
            #save time horizon
            self.timeHorizon = timeHorizon
            self.reset(timeHorizon=timeHorizon)
        if self.timeHorizon != timeHorizon: #if time horizon changed we need to resample
            #save time horizon
            self.timeHorizon = timeHorizon
            self.reset(timeHorizon=timeHorizon)
        # if same time horizon and already generated we only access the values
        if ret == 'OffLine':
            return self.demandScenarioOff
        elif ret == 'OnLine': 
            return self.demandScenarioOn
        else:
            raise ValueError('retailer not available.')
        
    #Time Horizon check
    def checkTimeHorizon(self,timeHorizon):
        if timeHorizon%7: #if not multiple of 7 it will raise the error
            raise ValueError('The environment is weekly based. TimeHorizon must be multiple of 7')