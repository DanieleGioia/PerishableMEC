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

### ${\color{red}{\text{Bug on Table 5 and 6 on:}}}$ $\text{'On the value of multi-echelon inventory management strategies for perishable items with on-/off-line channels'}$

The code associated with the numerical simulations related to the heuristic approaches (Section 4.2) in the article "On the value of multi-echelon inventory management strategies for perishable items with on-/off-line channels" had a bug in the estimation of the expected value, not achieving the claimed accuracy over the 35-period sliding window employed on the evaluation of heuristics approaches. The stopping criterion for the difference between the minimum and maximum values of the statistic associated with the expected value was blocked by a limit on the maximum number of simulated steps (1400), which was insufficient to guarantee a width of 0.02%, as claimed. Fluctuations of the expected value statistic, and thus of the objective function itself, might affect the optimization strategy by excessive fluctuations and biased function evaluations. We repeated the experiments with a maximum number of steps ten times larger, equal to 14000, using the same stopping criterion and optimization strategy presented in Gioia and Minner (2023). For the out-of-sample evaluation, we increase the 7000-period-long horizon five-fold to 35000. Evaluation and optimization of the full design of experiments are here presented in an updated version of Tables 5 and 6 from Gioia and Minner (2023).
Conclusions and remarks in Gioia and Minner (2023) remain valid, but some values have changed slightly. For example, the waste reduction of the BSP policy for a 5-period shelf-life compared to the COP policy has decreased, while the profit values of many multi-echelon policies have improved, as they are more prone to non-convergence of the expected value estimate due to more complex dynamics during simulation than single-echelon policies. It is also reasonable to point out that the very choice of optimization algorithm is practically a hyperparameter of the study and that, using non-surrogate techniques, different results might be obtained.

**Table 5 (Precise): Average profit and waste (Profit|Waste) per period with respect to different subsets of parameters and policies. Values normalized w.r.t. COP (profit, higher = better | waste smaller = better). COP values presented raw.**

|                   | Subset | COP        | BSP       | FPL\_l     | FPC\_l     | FPL2K\_l   | SP\_l      | SC\_l      | SP2K\_l    |
|-------------------|--------|------------|-----------|------------|------------|------------|------------|------------|------------|
| **On/Off**        | 80/20  | 430 \| 20.8| -1.4 \| -2.3| 0.3 \| -3.1| 0.5 \| -7.6| 0.1 \| -1.7| 0.9 \| -8.7| 0.9 \| -1.6| 0.7 \| -5.6|
|                   | 50/50  | 418 \| 24.7| -2.5 \| 3.9 | 0.4 \| -9.5| 1.0 \| -12.2| 0.4 \| -7.7| 1.4 \| -13.4| 1.6 \| -9.8| 1.6 \| -8.0|
|                   | 20/80  | 407 \| 27.3| -3.6 \| -0.1| -3.8 \| -5.2| -1.2 \| -9.0| -3.2 \| -3.4| -1.9 \| 1.2| -0.1 \| -4.0| -0.2 \| 1.7|
| **$\rho$**        | -0.5   | -          | -         | 0 \| -12.8 | 1.6 \| -17.3| 0.8 \| -12.1| 1.4 \| -12.4| 1.9 \| -9.6| 1.8 \| -10.1|
|                   | 0      | 418 \| 24.3| -2.4 \| 0.5| -0.9 \| -6.0| 0.2 \| -10.3| -0.8 \| -3.4| 0.2 \| -6.9| 0.8 \| -4.7| 0.7 \| -1.6|
|                   | 0.5    | -          | -         | -2 \| 0.3  | -1.3 \| -1.8| -2.3 \| 2.0 | -0.9 \| -0.8| -0.1 \| -1.9| -0.1 \| 0.1|
| **LIFO/FIFO**     | 50/50  | 425 \| 21.8| -2.1 \| 9.3| -1.4 \| -1.4| -0.1 \| -6.8| -1.0 \| -2.2| -0.2 \| 0.0| 0.4 \| -1.1| 0.5 \| 0.8 |
|                   | 90/10  | 411 \| 26.7| -2.7 \| -6.3| -0.5 \| -9.7| 0.5 \| -11.9| -0.6 \| -6.0| 0.8 \| -11.9| 1.3 \| -8.6| 1.1 \| -7.3|
| **cv**            | 0.6    | 440 \| 18.1| -1.1 \| 0.0| 0.1 \| -11.2| 1.0 \| -15.3| 0.3 \| -9.1| 0.4 \| -7.3| 1.0 \| -5.5| 0.8 \| -2.6|
|                   | 0.9    | 396 \| 30.4| -3.8 \| 1.2| -2.1 \| -2.9| -0.7 \| -6.3| -1.9 \| -1.4| 0.1 \| -6.1| 0.7 \| -5.0| 0.8 \| -4.3|
| **SL**            | 3      | 402 \| 28.5| -4.9 \| 8.0 | -3.2 \| 2.2 | -1.7 \| -1.2| -3.0 \| 5.4 | -0.1 \| -4.1| 0.7 \| -2.2 | 0.7 \| -0.8 |
|                   | 5      | 434 \| 20.0| -0.1 \| -9.6| 1.2 \| -17.7| 1.9 \| -21.6| 1.3 \| -18.1| 0.5 \| -9.9| 1.0 \| -9.6 | 0.9 \| -7.7 |
| **$\mathsf{newsR}$** | 0.75  | 662 \| 41.8| -2.3 \| 1.4 | -1.3 \| -5.0| -0.4 \| -9.3| -1.1 \| -3.5 | 0.0 \| -5.8| 0.4 \| -4.5 | 0.6 \| -3.6 |
|                   | 0.25  | 174 \| 6.7 | -2.8 \| -3.4 | 0.5 \| -12.3| 2.4 \| -11.8| 0.3 \| -9.5 | 1.4 \| -10.7| 2.4 \| -9.7 | 1.7 \| -3.9 |

**Table 6 (Precise): Percentage of relative improvement of profit and waste (Profit|Waste) per period with respect to different subsets of parameters and policies. Values normalized w.r.t. COP (profit, higher = better | waste smaller = better). COP values presented raw.**

|                   | Subset | COP        | BSP       | FPL\_l     | FPC\_l     | FPL2K\_l   | SP\_l      | SC\_l      | SP2K\_l    |
|-------------------|--------|------------|-----------|------------|------------|------------|------------|------------|------------|
| **On/Off**        | 80/20  | 430 \| 20.8| -1.8 \| -4.3| 0.4 \| -7.9| 0.8 \| -9.9| 0.2 \| -5.3| 1.5 \| -8.6| 1.5 \| -1.9| 1.2 \| -2.7|
|                   | 50/50  | 418 \| 24.7| -3.0 \| 1.6 | 0.9 \| -12.5| 1.9 \| -13.6| 0.8 \| -8.9| 2.2 \| -12.1| 2.4 \| -12.0| 2.4 \| -7.0|
|                   | 20/80  | 407 \| 27.3| -4.2 \| -1.8| -3.6 \| -10.2| -0.4 \| -13.8| -3.2 \| -9.8| -1.9 \| -4.0| 0.4 \| -6.1| -0.4 \| -0.9|
| **$\rho$**        | -0.5   | -          | -         | 1 \| -17.0 | 2.9 \| -20.4| 1.5 \| -14.1| 2.3 \| -14.8| 2.9 \| -12.8| 2.7 \| -11.5|
|                   | 0      | 418 \| 24.3| -3.0 \| -1.5| -0.8 \| -9.8| 0.8 \| -14.2| -0.8 \| -6.9| 0.6 \| -8.4| 1.2 \| -6.1| 1.0 \| -3.6|
|                   | 0.5    | -          | -         | -2 \| -3.9  | -1.4 \| -2.7| -2.9 \| -3.0 | -1.1 \| -1.5| 0.0 \| -1.1| -0.5 \| 4.5 |
| **LIFO/FIFO**     | 50/50  | 425 \| 21.8| -2.9 \| 5.6| -1.4 \| -7.6| 0.3 \| -11.9| -1.1 \| -8.0| -0.1 \| -3.3| 0.8 \| -4.5| 0.6 \| -0.7 |
|                   | 90/10  | 411 \| 26.7| -3.1 \| -8.6| -0.1 \| -12.8| 1.3 \| -13.0| -0.4 \| -8.0| 1.3 \| -13.2| 2.0 \| -8.8| 1.5 \| -6.4 |
| **cv**            | 0.6    | 440 \| 18.1| -1.1 \| -5.5| 0.6 \| -16.3| 1.8 \| -18.1| 0.8 \| -12.7| 0.7 \| -11.5| 1.6 \| -8.1| 1.2 \| -7.2 |
|                   | 0.9    | 396 \| 30.4| -4.9 \| 2.5 | -2.1 \| -4.1| -0.3 \| -6.8| -2.2 \| -3.3| 0.5 \| -5.0| 1.2 \| -5.3| 1.0 \| 0.1  |
| **SL**            | 3      | 402 \| 28.5| -6.3 \| 6.3 | -3.8 \| 0.7 | -1.8 \| -0.6| -3.7 \| 4.2 | 0.1 \| -4.6| 1.2 \| -2.2 | 0.8 \| -1.1 |
|                   | 5      | 434 \| 20.0| 0.3 \| -9.2 | 2.2 \| -21.1| 3.3 \| -24.3| 2.2 \| -20.2| 1.1 \| -11.9| 1.6 \| -11.1 | 1.3 \| -6.0 |
| **$\mathsf{newsR}$** | 0.75  | 662 \| 41.8| -2.5 \| 0.6 | -1.5 \| -7.0| -0.5 \| -11.4| -1.2 \| -5.7 | -0.1 \| -5.6| 0.4 \| -3.9 | 0.5 \| -2.6 |
|                   | 0.25  | 174 \| 6.7 | -3.5 \| -3.5 | -0.1 \| -13.5| 2.0 \| -13.5| -0.2 \| -10.3 | 1.3 \| -10.9| 2.4 \| -9.5 | 1.6 \| -4.5 |

### ${\color{blue}{\text{Additional notes on:}}}$ $\text{'On the value of multi-echelon inventory management strategies for perishable items with on-/off-line channels'}$

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