# PerishableMEC

This library addresses the inventory control problem for perishable products in a Multi-Echelon/Channel (MEC) setting. It supports both online and offline channels, with an option to model a multi-echelon structure utilizing an Online-Fulfillment-Center (OFC) for decision-making and as an online retailer. Additionally, it can simulate a single-echelon fashion where there is no OFC.
The library offers flexibility in modeling various offline retailers managed by a single OFC. However, note that allocation policies for multiple offline retailers require rationing and they are not currently available. The generation of correlated scenarios too is currently only available for a single offline channel together with the online channel. Contributions and developments in this area are encouraged and welcomed.


This library was crafted by me starting from a blank page. I did my best to provide a useful README and adequate comments. If you're a researcher or an academic enthusiast, feel free to dive in and use this for your research endeavors. All I ask is for some credit where it's due! The code supports the following article. If you employ any part of this code elsewhere, we recommend citing the original article.

```Bibtex
@article{gioia2023Onthe,
  title={On the value of multi-echelon inventory management strategies for perishable items with on-/off-line channels.},
  author={Gioia, Daniele Giovanni and Minner, Stefan},
  journal={Transportation Research Part E: Logistics and Transportation Review},
  volume={180},
  pages={103354},
  year={2023},
  publisher={Elsevier}
}
```

## Code Structure

```bash

|____configurations
| |____conf_Producers_Sing.json
| |____conf_Store_Depot.json
| |____conf_Store_Ind.json

|____env
| |______init__.py
| |____dailySimulation.py

|____managers
| |______init__.py
| |____DepotManager.py
| |____InventoryManager.py
| |____ScenarioGeneratorRandom.py
| |____StatManager.py
| |____SupplyManager.py

|____policies
| |______init__.py
| |____PolicyMultiEchelon.py
| |____PolicySingleEchelon.py
| |____SingleEchCOP_BSP.py
| |____SingleRetailerDepot.py

|____README.md
|____main_example.py

```

## Configuration

**conf_Producers_Sing.json** defines a single ordered product, detailing its lead time for delivery, shelf life starting from the order time, and unit cost. Please note, the delivered product's shelf life equals the original shelf life minus the lead time.

**conf_Store_\*** files detail configurations with or without a depot. They outline both online and offline channel characteristics as follows:

- Demand distribution specifics, including the expected value and standard deviation. Currently supports either negative binomial or Gaussian types, though further generalizations can be implemented.
- Internal lead time (RLT) for depot configurations, representing additional time needed to deliver items from the depot to the offline physical retailer.
- Retailer-specific sell prices, markdowns, or disposal costs.
- Consumer behavior patterns in terms of LIFO/FIFO distribution. The number of LIFO (and accordingly FIFO) is modeled by sampling a binomial distribution with parameters equal to the demand number and success percentage, which can be either stochastic 'LS' (beta distributed, generating a beta-binomial distribution) or fixed 'LF'.

## Simulation environment

**DailySimulation.py** is a [gym](https://github.com/openai/gym)-based sequential simulation environment. Each period is assumed to be a day, but such an interpretation is arbitrary. 

Each necessitates the following parameters:

1. `retailers`: The class for managing all retailers in the simulation.

2. `depot`: The class for managing the depot in the simulation (multi-echelon). None if there is no depot (single-echelon).

3. `statManager`: This is required for handling statistics throughout the simulation.

4. `timeHorizon`: Specifies the maximum length of the simulation.

5. `flagPrint`: This boolean value controls the verbosity of the simulation. If set to `True`, it will recursively apply to all components of the simulation and provide a comprehensive print-out of the simulation.

Below is an illustrative example of a printed simulation step in a multi-echelon setting:

```bash

Inventory depot before dispatch:
Product Stored
	 14.0 items with  1 Residual shelf life
	 70.0 items with  2 Residual shelf life
	 109.0 items with  3 Residual shelf life
	 216.0 items with  4 Residual shelf life
Oredered by Depot:  [  0.   0.   0. 197.]
[  0.   0. 141.]  units of product dispatched to retailer:  OffLine
[ 287.  443. 3888.]  TOTAL of units of product dispatched to retailer:  OffLine
Total scrapped so far 1148.0
Cost of the day  246.25
Total cost so far  10747.5
-------------DAY  41   ENDS -------
------------------New day Begins------------------------

 Day 42 
 inventory depot:
Product Stored
	 14.0 items with  1 Residual shelf life
	 70.0 items with  2 Residual shelf life
	 109.0 items with  3 Residual shelf life
	 75.0 items with  4 Residual shelf life
Demand:  48.0
Scrapped by Depot:  0.0
 Depot:
Sold:   [14. 34.  0.  0.]  Scrapped:  0.0
No purchase:  0
Total sold so far 2030.0
Profit of the day  240.0
------------Night at the Depot-------------
------------------------------------------
RETAILER:  OffLine

Day 42 
Inventory:
Product Stored
	 0.0 items with  1 Residual shelf life
	 77.0 items with  2 Residual shelf life
 shipped by depot to retailer  OffLine :
Waiting for: 
	 [ 0.  0. 82.]  items have just arrived.
	 [  0.   0. 141.]  items, expected in 1 days
Demand:  127.0
 Dispatched/Ordered(if no depot) product:  [  0.   0. 141.]  Sold:   [ 0. 77. 50.]  Scrapped:  0.0
No purchase:  0
Total dispatched by the depot/orederd by retailer so far  4618.0
Total scrapped so far 547.0
Total sold so far 3898.0
Profit of the day  571.5
------------------------------------------
CashFlow of the day  565.25
State observation:  {'Depot': {'inventory': array([ 36., 109.,  75.,   0.]), 'ordered': array([[  0.,   0.,   0., 244.],
       [  0.,   0.,   0., 141.],
       [  0.,   0.,   0., 197.]])}, 'OffLine': {'inventory': array([ 0., 32.,  0.]), 'dispatched': array([  0.,   0., 141.])}}

```

Simulation length can be set as follow

```python
#FULL HORIZON SIMULATED
env.setTest()
#SIMULATION STOPS IF CONVERGENCE CONDITIONS ARE SATISFIED
env.setLearn()
```

Specifically, under learning hypotheses, the simulation stops if the difference between the maximum and minimum value of the estimated expected value of profit in a 35-period sliding window is less than 0.025% of the current estimation. Such hyperparameters can be set in the **StatManager** class, modifying _self.eps_ and _self.window_.

For each step, the simulation is recursively performed over all the components (retailers and depot, if any), and dynamics are organized as follows:

1. Order and dispatch decisions are made according to replenishment and dispatch policies.

2. Items ready to be delivered after the necessary lead time are handed over.

3. LIFO and FIFO clients are simulated together with 'daily sales'.

4. The shelf life of stored items is reduced and expired items are scrapped.

5. Statistics are computed.

6. The state of the system is observed.

## Policies

This library provides a comprehensive set of policies designed for scenarios where a retailer operates through both an online and an offline channel. The retailer could either be an independent entity or function as an online fulfillment center, serving simultaneously as a depot.

Two abstract classes are given **PolicyMultiEchelon.py** and **PolicySingleEchelon.py** to formalize the minimum requirement a policy class must have. Whatever the policy (Value-Function approximation-based, Policy-Function approximation-based, etc.. ), we need a _decide_ method that computes an order/dispatch decisions dict from the observation dict. An example of the observation dictionary is hereafter provided: 

```bash
State observation:  {'Depot': {'inventory': array([ 36., 109.,  75.,   0.]), 'ordered': array([[  0.,   0.,   0., 244.],
       [  0.,   0.,   0., 141.],
       [  0.,   0.,   0., 197.]])}, 'OffLine': {'inventory': array([ 0., 32.,  0.]), 'dispatched': array([  0.,   0., 141.])}}

```

For each retailer (offline/online), we observe the ordered queue and the current inventory.

### Single-echelon policies

Let us notationally assume we observe the following state of the system for each retailer $k$ in a single-echelon approach

$$ \mathsf{R}^k_t = \left[O_k^{\mathsf{LT-1}} ,\dots, O_k^0 | I_k^{\mathsf{SL-1}} ,\dots,  I_k^1 \right], $$

where $O_k^l$ are the ordered items that will arrive in $l$ periods and $I_k^r$ the current physical inventory for each residual shelf life $r$.

The **SingleEchCOP_BSP** class requires the retailers and producer characteristics and, as default, provides a constant order policy that always orders the same amount of products.
For example, given the offline and online channels, if we set

```python
policy = SingleEchCOP_BSP(store_setting, producer,{}) 
policy.setParameters(*policy.xToParams([100,100]))
```

the policy will always order 100 items per period per retailer.

if we set

```python
policy.setBSP('k')
```

for that channel it will rather order in a base-stock fashion, thus ordering

$\left[ x_k - \sum_r I_k^r  - \sum_l O_k^l \right]^+$

We refer to the supporting article for more analytical details.

### Multi-echelon policies

When we consider a multi-echelon system, the observed state of the system is

$S_t = \left[\mathsf{DC}_t|\mathsf{RT}_t  \right],$

where

$\mathsf{RT}_t = \left[ O^{\mathsf{RLT}-1,\, \mathsf{SL - RLT}} ,\dots, O^{\mathsf{RLT}-1,\,1},\dots, O^{0,1} | I^{\mathsf{SL - RLT}-1},\dots , I^{1}  \right]$

is the state of the system of the offline retailer, with

- $\mathsf{RLT}$: The delay between product delivery from the distribution center and arrival at the physical store.
- $O^{l,r}$: The dispatched items that will arrive in $l$ periods with residual shelf life $r$.
- $I^r$: The current physical inventory with residual shelf life $r$.

and

$\mathsf{DC}_t = \left[O_d^{\mathsf{LT-1}} ,\dots, O_d^0 | I_d^{\mathsf{SL-1}} ,\dots,  I_d^1 \right]$

the OFC state of the system.

The **SingleRetailerDepot** class allow for different kind of joint order and dispatch policies. For example, if we want to order a BSP-based quantity

$$\bigg[ x_0 - \sum_r \big( I_d^r + I^r\big) - \sum_l \big( O_d^l + \sum_{r} O^{l,r}\big)\bigg]^+$$

and allocate to the offline channel according to a BSP request and a LIFO internal issuing policy

$$ \text{min} \bigg[ \big[ x_1 - \sum_r I^r -\sum_l \sum_r O^{l,r} \big]^+ , \sum_r I^r_d \bigg], $$

we may set the policy as follow

```python
policy = SingleRetailerDepotPolicy(store_setting, producer, {}, {})
policy.setOrderPolicy('BSP') 
policy.setDispatchPolicy('BSP') 
policy.setInnerIssuing('LIFO')
policy.setParameters(*policy.xToParams([x_0,x_1]))
```

If we want to weigh differently new and young on-hand items at retailer $k$ and allocate according to the following policy

$$ \text{min} \left[ \big[ x_1 - x_3^\mathsf{old} \sum_{r = 1}^{\mathsf{SL} - \mathsf{RLT} -x_2} I_k^r - x_4^\mathsf{new}\sum_{r = \mathsf{SL}- \mathsf{RLT} -x_2+1}^{\mathsf{SL}- \mathsf{RLT}-1} I_k^r - \sum_l\sum_r O_k^{l,r} \big]^+, \sum_r I^r_d \right], $$

while ordering according to a constant policy $x_0$, we may set

```python
policy = SingleRetailerDepotPolicy(store_setting, producer, {}, {})
#policy.setOrderPolicy('COP') #already COP by default
policy.setDispatchPolicy('BSP') 
policy.setInnerIssuing('LIFO')
policy.set2k()
policy.setParameters(*policy.xToParams([x_0,x_1,x_2,x_3,x_4]))
```

We refer to the supporting article for more analytical details and many other possible policies.

## Example

In **main_example**, a ready-to-use example is provided. Several configurations and policies are implemented and can be selected by the _pol_ and _conf_ variables. The final outputs are the average profit and waste (with an initial transient period removed). Furthermore, a plot of the average profit is provided to investigate the convergence properties.
Such an example is also useful to understand how to set the correlation. Specifically, when a _ScenarioManager_ is initialized, we use the first two moments of the demand distribution of the channels and their type. The instance of the class will build a Gaussian-copula-based correlation according to the linear correlation parameter we set. E.g.,

```python
scenarioMgr = ScenarioGenerationCorr(store_setting['OnLine']['Distr'], store_setting['OnLine']['ev_Daily'],store_setting['OnLine']['std_Daily'],store_setting['OffLine']['Distr'],store_setting['OffLine']['ev_Daily'],store_setting['OffLine']['std_Daily'],LINEAR_CORR_PARAM)
```

Currently, only Gaussian copula and a restricted set of marginal distributions are available. Further improvements on the scenario generator and its interface are welcomed.


## ${\color{blue}{\text{Additional notes on:}}}$ $\text{'On the value of multi-echelon inventory management strategies for perishable items with on-/off-line channels'}$

The range of values for the coefficient of variation in Gioia and Minner (2023) is modeled by considering an adjusted daily adaptation of the weekly estimated values from Broekmeulen and van Donselaar (2019). Specifically, considering an independent daily adaptation, with our settings of mean demand $\mu_\text{daily} = 100$ we would have
```math
 \text{cv}_{\text{daily}} = \frac{ \sigma_{\text{daily}} }{ \mu_{\text{daily}} } = \frac{\sigma_{\text{weekly}}}{\mu_\text{daily}\sqrt{7}} = \frac{\mu^{0.77}_\text{weekly}0.7}{\mu_\text{daily}\sqrt{7}} = \frac{7^{0.77}\mu^{0.77}_\text{daily}0.7}{\mu_\text{daily}\sqrt{7}} = \frac{7^{0.77}0.7}{\sqrt{7}}\mu^{-0.23}_\text{daily} = 0.41
```
according their equation $\sigma_{\text{weekly}}=0.7\mu_{\text{weekly}}^{0.77}$. However, we deal with products with high daily sales (and low shelf life) and they state and report that under these assumptions perishables are correlated to higher correspondent daily standard deviations. Unfortunately, for confidentiality reasons, they normalize their data and provide only aggregated statistics, making more specific deductions complex. To provide meaningful experiments, we assume higher values and investigate more than one option ($\text{cv}_{\text{daily}} = 0.6, 0.9$), focusing on the relative differences in their effects rather than absolute behaviors in a specific case study, where this very code can be used being part of the scientific contribution. 

```Bibtex
@article{broekmeulen2019quantifying,
  title={Quantifying the potential to improve on food waste, freshness and sales for perishables in supermarkets},
  author={Broekmeulen, Rob ACM and van Donselaar, Karel H},
  journal={International Journal of Production Economics},
  volume={209},
  pages={265--273},
  year={2019},
  publisher={Elsevier}
}
```
