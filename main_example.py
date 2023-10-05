from managers import *
from policies import *
from envs import *
import numpy as np
import json
import matplotlib.pyplot as plt

#Single source with or without depot. Notice how the number of character is not random and used to read the correct input.
conf = 'SingSourceDepot' # 'SingSourceInd' or 'SingSourceDepot'
#Policies available with an independent single echelon network: BSP,COP
#Policies available with a multi-echelon system with depot: FPL_(l or f), SP_(l or f), FPC_(l or f), SC_(l or f), FPL2K_(l or f)
pol =  'SC_l'
#Notice that current parameters of the policies are examples not optimized.

#output precision
np.set_printoptions(precision=3)
np.set_printoptions(suppress=True)

# Load setting
fp = open(f"./configurations/conf_Producers_"+conf[:4]+".json", 'r')
prod_setting = json.load(fp)
fp.close()
fp = open("./configurations/conf_Store_"+conf[10:]+".json", 'r')
store_setting = json.load(fp)
fp.close()

#single producer. Notice that is possible to generalize to multiple producers by means of a dictionary of suppliers with different costs/lead-time/shelf-life. Such a features is currently not implemented.
producer = prod_setting['A']

#Print flag (pedantic output, step by step)
flagPrint = True

#Depot? self-configuring flag to either use or not the Depot according to the conf variable
flagDepot = (conf[-5:] == 'Depot')
#######Inizialization

#Related time horizon of the simulation
Weeks = 500 #number of MAXIMUM weeks tested
timeHorizon = 7*Weeks #time horizon in days
transientDays = 3*(producer['SL'] + producer['LT']) #starts accumulating statistics after this number of periods

#If the simulation aims to learn the policy, it will stop after reaching a specific tolerance. Conversely, in a test setting, 
#the horizon will be exhausted. Notice that when learning, a policy may be simulated under hundreds of different paramenters, with a large computational cost

#Scenario generation with correlated demand for Online and Offline retailers.
#We need to pass the kind of distribution and the two first moments. Currently it only accept a restricted set of bi-parametric distributions (Normal or NegativeBinomial)
scenarioMgr = ScenarioGenerationCorr(store_setting['OnLine']['Distr'], store_setting['OnLine']['ev_Daily'],store_setting['OnLine']['std_Daily'],store_setting['OffLine']['Distr'],store_setting['OffLine']['ev_Daily'],store_setting['OffLine']['std_Daily'],-0.5)

if flagDepot: #Depot conf.
    ####
    #Retailers
    ####   

    #Each OffLine retailer needs a ScenarioManager, an InventoryManager and a supplyManager for each treated product and a consumerManager
    retailers = {}
    #Separation between online and offline
    if 'OnLine' not in store_setting.keys():  raise ValueError('Depot must be a vendor on the OnLine channel.')
    offLine_setting = {key: store_setting[key] for key in store_setting.keys() if str('OnLine').find(key)}
    #
    for k in offLine_setting.keys():
        #The mangers must be albe to deal with the max possible shelf life
        #Invetory manager
        invManager = InventoryManager(producer['SL'] - producer['LT'] - store_setting.get(k)['RLT'])
        #Supply managers 
        supManager = SupplyManager(store_setting.get(k)['RLT'], producer['SL'] - producer['LT']  - store_setting.get(k)['RLT'])
        #Prices setting
        pricesRetail = {} #retail
        markdownRetail = {} 
        pricesRetail = store_setting.get(k)['P']
        markdownRetail = store_setting.get(k)['MD']
        #Retailer instance
        retailers[k] = RetailManager(k,scenarioMgr,store_setting.get(k)['LIFO%'],invManager,supManager,timeHorizon,pricesRetail,markdownRetail)

    ####
    #Depot (OnLine)
    ####

    #Invetory managers
    invManager = InventoryManager(producer['SL'] - producer['LT'])
    #Supply manager and cost of the items
    supManager = SupplyManager(producer['LT'],producer['SL'] - producer['LT'])
    cost_depot = producer['C']
    #specifics of the Depot must be inside the 'OnLine' indexed dictionary
    #price and md
    priceDepot = store_setting['OnLine']['P']
    markdownDepot = store_setting['OnLine']['MD']
    #delivery times x retail
    deliveryTimes = {}
    for k in offLine_setting.keys():
        deliveryTimes[k] = store_setting.get(k)['RLT']
    #Depot initialization
    depot = DepotManager(invManager,supManager,deliveryTimes,cost_depot,timeHorizon,scenarioMgr,store_setting['OnLine']['LIFO%'],priceDepot,markdownDepot)

else: # No depot conf
    depot = None
    #Each retailer needs a ScenarioManager, an InventoryManager and a supplyManager for each treated product and a consumerManager
    retailers = {}
    for k in store_setting.keys():
        #Invetory manager
        invManager = InventoryManager(producer['SL'] - producer['LT'])
        #Supply managers
        supManager = SupplyManager(producer['LT'],producer['SL'] - producer['LT'])
        #Prices and Qualities setting
        pricesRetail = {} #retail
        markdownRetail = {} 
        pricesRetail = store_setting.get(k)['P']
        markdownRetail = store_setting.get(k)['MD']
        #Retailer instance
        costRetailer = producer['C']
        retailers[k] = RetailManager(k,scenarioMgr,store_setting.get(k)['LIFO%'],invManager,supManager,timeHorizon,pricesRetail,markdownRetail,costRetailer)


#####
##StatManager of the simulation
#####
statMgr = StatManager(store_setting, flagDepot)
statMgr.setTimeHorizon(timeHorizon)
#An head defines a transient period to discount the empty-inventory initial conditions
statMgr.setHead(transientDays) 

#######Inizialization - end


#####
# Sequential-env with daily dependent actions 
#####

##Example policies
if conf == 'SingSourceDepot':
    if pol[:2] == 'SP':
        x = [300,230]
        policy = SingleRetailerDepotPolicy(store_setting, producer, {}, {})
        policy.setDispatchPolicy('BSP')
        policy.setInnerIssuing('LIFO')
    elif pol[:2] == 'SC':
        x = [235,290,40]
        policy = SingleRetailerDepotPolicy(store_setting, producer, {}, {})
        policy.setDispatchPolicy('BSP')
        policy.setInnerIssuing('LIFO')
        policy.setCriticalOnline()
    elif pol[:2] == 'FP':
        x = [1150,300]
        policy = SingleRetailerDepotPolicy(store_setting, producer, {}, {})
        policy.setOrderPolicy('BSP') 
        policy.setDispatchPolicy('BSP') 
        if pol[2] == 'C':
            x = [800,230,30]
            policy.setCriticalOnline()
        elif pol[2:5] == 'L2K':
            policy.set2k()
            x = [800,230,1,0.6,1]
        elif pol[2] == 'L':
            pass
        else:
            raise ValueError('Policy not available')
    else:
        raise ValueError('Policy not available')
    #end if on policy type. now if on internal issuing
    if pol[-1] == 'l':
        policy.setInnerIssuing('LIFO')
    elif pol[-1] == 'f':
        policy.setInnerIssuing('FIFO')
    else:
        raise ValueError('Policy not available')

if conf == 'SingSourceInd':
    if pol == 'COP':
        x = [100,100]
        policy = SingleEchCOP_BSP(store_setting, producer,{}) 
    elif pol == 'BSP':
        x = [900,900]
        policy = SingleEchCOP_BSP(store_setting, producer,{})
        policy.setBSP('OnLine')
        policy.setBSP('OffLine')
    else:
        raise ValueError('Policy not available')

#from x to actions
policy.setParameters(*policy.xToParams(x))

######
###### 
#Dynamics
env = DailySimulation(retailers,depot,statMgr,timeHorizon,flagPrint)
#Learning? Testing?
# env.setTest()
env.setLearn()
scenarioMgr.reset(timeHorizon=timeHorizon)
env.setSeed('All',1)
done = False
obs = env.reset()



while not done:
    obs, reward, done, _ = env.step(*policy.decide(obs))
    if flagPrint:
        #pass
        input("Press Enter to continue")

#Convergence analysis and plot main metrics

hor = len(env.statMgr.avgProfitHist)
plt.plot(env.statMgr.avgProfitHist)
ax = plt.gca()
plt.title('Average profit convergence plot')
plt.xlabel('Simulated days')
plt.ylabel('Average daily profit')

print('Final average profit per period: ', env.getAverageProfit())
print('Scrapped items per period: ',env.getAverageScrapped())
