# PAPER_ANALYSIS.md

## Technical Analysis of the Reference Paper

**Paper:** Y. Wu, C. Zhang, L. Tong, X. Shi, "Location Optimization Based on Improved 3D DV-HOP Algorithm in Wireless Sensor Networks," *IEEE Access*, vol. 11, pp. 85525–85536, 2023. DOI: 10.1109/ACCESS.2023.3303569.
**Local copy:** `Location_Optimization_Based_on_Improved_3D_DV-HOP_Algorithm_in_Wireless_Sensor_Networks.pdf`

### How to read this document

- **Locations** are given as *Section / Equation / Figure / Table* plus the journal page number (pp. 85525–85536). PDF page *k* is journal page 85524 + *k*.
- Each statement carries one of three provenance tags:
  - **[PAPER]** The paper states it explicitly.
  - **[INTERP]** The paper states it in a way that needs interpretation. The interpretation is explained, and every one is listed as an open question in `IMPLEMENTATION_PLAN.md`.
  - **[MISSING]** The paper does not give it.
- Equations are transcribed **as printed**, typos included. Suspected typos are noted beside the equation, never silently corrected.
- Terminology follows the paper's abbreviations: AN = anchor node, UN = unknown node, KN = known node, SN = sensor node, HC = hop count, HD = hop distance, AHD = average hop distance, CR = communication radius, MCR = multiple communication radii, DHA = DV-HOP algorithm, TDS = three-dimensional space, PA = positioning accuracy, ART = average running time, OH = original hop.

---

## 1. Research problem and motivation

- **[PAPER]** DV-HOP is a *range-free* localization algorithm. It is simple, needs no extra ranging hardware and is cheap (Abstract, p. 85525; §III-A, p. 85527).
- **[PAPER]** Real WSNs are often deployed in three-dimensional terrain (deep sea, hills), and the nodes cannot be treated as lying on a plane (§I, p. 85525).
- **[PAPER]** 3D DV-HOP still has "significant positioning errors", especially when nodes are randomly distributed (§I, p. 85525; §III-A, p. 85528).
- **[PAPER]** The authors' error analysis (§III-A, p. 85529) lists five sources of error:
  1. Blind spots and *isolated nodes* caused by irregular node distribution.
  2. Dependence on the anchor ratio. Too many nodes inside an AN's CR make the AHD smaller than its true value.
  3. Integer hop counts are inaccurate. Nodes at very different distances inside one CR all count as "one hop".
  4. Paths are really broken lines, not straight lines. Using only the *nearest* AN's hop distance ignores the hop distance of the target KN.
  5. Error from the final coordinate estimation step (distance = HC × HD followed by multilateration / MLE).
- **[PAPER]** The authors conclude that the main factors are **HC, HD and the estimation method** (§III-B, p. 85529).

## 2. Objectives of the paper

**[PAPER]** (§I, p. 85526; §III-B, pp. 85529–85531):

1. Extend DV-HOP to a 3D network environment.
2. Reduce hop-count error by using **multiple communication radii (MCR)**, which make hop counts fractional ("decimalized").
3. Reduce hop-distance error by setting a **hop-count threshold** that discards anchors with large error, and by **weighting** the remaining anchors when computing each anchor's AHD.
4. Compute the UN-to-AN distance from the **median (mean) of two hop distances**.
5. Replace the MLE coordinate estimate with a **linearly-decreasing-inertia-weight PSO**, because MLE can hit a non-invertible matrix.
6. Evaluate the resulting algorithm, **HCMSPSO-DV-HOP**, by simulation.

**Naming note [PAPER]:** The same proposed algorithm appears as *HCMSPSO-DV-HOP* (Abstract, §III-B, Fig. 11) and *HCMCPSO-DV-HOP / HCMCPSO-DHA* (Figs. 12–13, §IV, §V). These look like spelling variants of one algorithm. The paper also defines an **intermediate** algorithm, **HCMCDV-HOP**: MCR + hop threshold + weighted AHD, but still using MLE (§III-B, p. 85529). HCMCDV-HOP is plotted separately in Fig. 12.

---

## 3. Traditional DV-HOP / 3D DV-HOP

Source: §III-A, pp. 85527–85528, Eqs. (1)–(6), Fig. 4.

### 3.1 Stage 1: minimum hop count by flooding [PAPER]

- Every AN floods a packet containing its own data. The AN's initial hop value is 0.
- A receiving node adds 1 to the hop value and forwards the packet.
- A node keeps only the **minimum** hop value received from each AN.
- Result: $h_{ij}$, the minimum hop count between every node and every AN.
- Fig. 4: if a node receives a packet from an AN it has already heard from, it compares, saves the smaller hop value, then applies "hop+1 and forward".

### 3.2 Stage 2: average hop distance (AHD)

**Eq. (1), 2D form (p. 85527) [PAPER]:**

$$Hopsize_i = \frac{\sum_{j=1, j\neq i}^{N}\sqrt{(x_i-x_j)^2+(y_i-y_j)^2}}{\sum_{j=1, j\neq i}^{N} h_{ij}}$$

**Eq. (3), 3D form (p. 85528) [PAPER]:** This is the form used for 3D DV-HOP.

$$Hopsize'_i = \frac{\sum_{j=1, j\neq i}^{N}\sqrt{(x_i-x_j)^2+(y_i-y_j)^2+(z_i-z_j)^2}}{\sum_{j=1, j\neq i}^{N} h_{ij}}$$

| Symbol | Meaning | Units |
|---|---|---|
| $(x_i,y_i,z_i)$, $(x_j,y_j,z_j)$ | Coordinates of anchors (KN) *i* and *j* | m |
| $h_{ij}$ | Minimum hop count between anchors *i* and *j* | hops (dimensionless) |
| $N$ | Number of anchor nodes | count |
| $Hopsize_i$, $Hopsize'_i$ | AHD of anchor *i* over the whole network | m/hop |

*Notation issue [PAPER]:* Below Eq. (1) the text calls the coordinates "$(x_1,y_1)$ and $(x_2,y_2)$", which does not match the $x_i, x_j$ in the formula. The meaning is still clear.

**[PAPER]** After the AHDs are computed, each UN adopts "the HD of the nearest AN" as its own hop distance (p. 85527). **[INTERP]** "Nearest" is taken to mean fewest hops, since that is the only kind of nearness a UN knows in range-free DV-HOP. Fig. 4 shows anchors broadcasting their AHD, but the tie-break rule is not stated.

### 3.3 Stage 3: distance estimate

**Eq. (2) (p. 85528) [PAPER]:**

$$d_{ij} = Hopsize_i \times h_{ij}$$

| Symbol | Meaning | Units |
|---|---|---|
| $d_{ij}$ | Estimated distance from UN *i* to anchor *j* | m |
| $Hopsize_i$ | Hop distance adopted by UN *i* (that of its nearest AN) | m/hop |
| $h_{ij}$ | Minimum hops from UN *i* to anchor *j* | hops |

*Notation issue:* Eqs. (1)/(3) use *i* for an anchor, but Eq. (2) uses *i* for an unknown node.

### 3.4 Stage 4: coordinate estimation ("MLE")

**Eq. (4) (p. 85528) [PAPER]:** sphere equations for the unknown position $(x,y,z)$:

$$\sqrt{(x-x_k)^2+(y-y_k)^2+(z-z_k)^2} = d_k,\quad k = 1,2,3$$

Only three are printed. Eq. (6) generalises to *n* anchors.

**Eq. (5) [PAPER]:**

$$X = (A^TA)^{-1}A^Tb$$

**Eq. (6) [PAPER]**: rows $k = 1,\dots,n-1$, with anchor *n* as the reference:

$$A = \begin{bmatrix} 2(x_1-x_n) & 2(y_1-y_n) & 2(z_1-z_n)\\ \vdots & \vdots & \vdots \\ 2(x_{n-1}-x_n) & 2(y_{n-1}-y_n) & 2(z_{n-1}-z_n)\end{bmatrix},\quad
b = \begin{bmatrix} x_1^2-x_n^2+y_1^2-y_n^2+z_1^2-z_n^2+d_n^2-d_1^2\\ \vdots \\ x_{n-1}^2-x_n^2+y_{n-1}^2-y_n^2+z_{n-1}^2-z_n^2+d_n^2-d_{n-1}^2\end{bmatrix}$$

| Symbol | Meaning | Units |
|---|---|---|
| $X = [x,y,z]^T$ | Estimated UN coordinates | m |
| $(x_k,y_k,z_k)$ | Coordinates of anchor *k* | m |
| $d_k$ | Estimated distance UN → anchor *k* (Eq. 2) | m |
| $n$ | Number of anchors used | count |
| $A$ | $(n-1)\times 3$ matrix | m |
| $b$ | $(n-1)\times 1$ vector | m² |

Notes:
- **[PAPER]** The paper calls this step *maximum likelihood estimation (MLE)*. Mathematically, Eq. (5) is the linear least-squares solution of the linearised system. The paper's term will be kept in all project documents.
- **[INTERP]** Solving for 3 unknowns needs $n-1 \ge 3$, so **at least 4 anchors** that are not coplanar. The paper never states this requirement.
- **[PAPER]** Fig. 4 has a branch: "The node cannot be located" when a node received no anchor information.

---

## 4. Improved algorithm: HCMCDV-HOP → HCMSPSO-DV-HOP

Source: §III-B, pp. 85529–85531, Eqs. (7)–(16), Figs. 5–7.

### 4.1 Improvement 1: multiple communication radii (MCR), fractional hop counts

**[PAPER]** Text from p. 85530, column 1:

> "In the first stage, the AN is introduced with three communication radii to broadcast data. During network initialization, AN first broadcast packet information to the network at a CR of R/3, while recording the hops' quantity in adjacent AN as 1/3 hops. After time F, the AN then propagates the packet information to the network at the CR 2R/3. If the node receiving the AN does not have the AN's HC, the HC will be recorded as 2/3. If there is a hop value, the original hop (OH) will be forwarded. After passing through time T again, the AN propagates the packet information to the network at the CR R. After receiving AN information from neighboring nodes, if it is found that there are no data packets stored for the AN, the HC is marked as 1. If there is HC, the OH value will be forwarded through the above process, and each node can obtain the minimum HC between the AN."

What this gives:

| Distance $d$ from broadcasting AN | Hop value recorded |
|---|---|
| $d \le R/3$ | 1/3 |
| $R/3 < d \le 2R/3$ | 2/3 |
| $2R/3 < d \le R$ | 1 |

- **[PAPER]** Fig. 5 shows the idea: (a) one radius, (b) three concentric radii around an anchor.
- **[INTERP] Ambiguity:** The text says **anchors** broadcast at three radii. It does not say how hop values grow beyond the first hop. Possibilities:
  - Only the AN→neighbour link is fractional, and relaying nodes add 1 per hop.
  - Every link is weighted 1/3, 2/3 or 1 by its length, which would need every node to transmit at three power levels.

  See open question Q1 in the plan.
- **[INTERP]** Times *F* and *T* are only for ordering the broadcasts. They have no numerical role in a centralised simulation.

### 4.2 Improvement 2: hop-count threshold for discarding anchors

**Eq. (7) (p. 85529) [PAPER]:**

$$t_i = \max\left(\frac{d_{i1}}{R},\frac{d_{i2}}{R},\dots,\frac{d_{iM}}{R}\right)$$

| Symbol | Meaning | Units |
|---|---|---|
| $t_i$ | Hop-count threshold of anchor *i* | hops |
| $M$ | "the endpoints' quantity in a TDS" | count |
| $d_{im}$ | "the distance from each endpoint to AN *i*" | m |
| $R$ | Communication radius | m |

- **[PAPER]** If the hop count from another AN to target AN *i* is greater than $t_i$, the path is taken to be arranged in "multiple lines" (strongly bent). That AN is then **not used** when computing $Hopsize_i$ (p. 85529).
- **[INTERP] Ambiguity:** "Endpoints in a TDS" most plausibly means the **8 vertices of the cubic deployment region**, so M = 8. A second reading is "the other anchors". See Q2.

### 4.3 Improvement 3: weighted average hop distance of anchors

**Eq. (8) (p. 85529) [PAPER]:**

$$c_{ij} = \frac{1}{d_{ij}/R - hops_{ij}}$$

**Eq. (9) [PAPER]**, transcribed as printed:

$$w_{ij} = \frac{c_{ij}}{\sum_{l\neq i}^{s} c_{ij}}$$

**Eq. (10) [PAPER]:**

$$Hopsize_i = \sum_{j\neq i}^{s} w_{ij}\times\frac{d_{ij}}{hops_{ij}}$$

| Symbol | Meaning | Units |
|---|---|---|
| $c_{ij}$ | Weight coefficient of AN *j* when computing the AHD of KN *i* | 1/hops |
| $d_{ij}$ | **True** distance between anchors *i* and *j* (both positions known) | m |
| $hops_{ij}$ | Hop count between anchors *i* and *j*. **[INTERP]** These are the MCR hop values of §4.1 | hops |
| $R$ | Communication radius | m |
| $w_{ij}$ | Normalised weight | dimensionless |
| $s$ | Number of KNs (anchors). **[INTERP]** The anchors that pass the Eq. (7) threshold | count |
| $Hopsize_i$ | Weighted AHD of anchor *i* | m/hop |

Analysis:
- **[INTERP] Typo in Eq. (9):** The sum runs over *l*, but the summand is written $c_{ij}$. Read literally, the denominator would be $(s-1)\,c_{ij}$, which makes every $w_{ij}$ equal to $1/(s-1)$ and the weighting pointless. The intended form is almost certainly $\sum_{l\neq i} c_{il}$. See Q4.
- **[INTERP] Sign of Eq. (8):** Each link spans at most *R* (or *R*/3, 2*R*/3 at the fractional levels), so $hops_{ij} \ge d_{ij}/R$ in general. The denominator is therefore **≤ 0** and every $c_{ij}$ is negative. Eq. (9) normalises by the sum of these same-sign values, so all $w_{ij}$ come out **positive** and sum to 1. Anchors whose hop count is close to the straight-line value $d_{ij}/R$ (straighter paths) get **larger** weights. This matches the paper's stated intent, so the literal formula can be implemented without any change.
- **[INTERP] Singularity:** If $hops_{ij} = d_{ij}/R$ exactly, Eq. (8) divides by zero. With continuous random positions this has probability zero, but values arbitrarily close to it can occur. The paper does not cover this. See Q5.
- **[MISSING]** The paper does not say what to do if the threshold removes **every** other anchor ($s = 0$). See Q3.

### 4.4 Improvement 4: UN-to-AN distance from two hop distances

**Eq. (11) (p. 85530) [PAPER]:**

$$d_{ij} = \tfrac{1}{2}\left(Hopsize_i + Hopsize_j\right)\times h_{ij}$$

| Symbol | Meaning | Units |
|---|---|---|
| $d_{ij}$ | Estimated distance from UN *i* to AN *j* | m |
| $Hopsize_j$ | AHD of the target anchor *j* (Eq. 10) | m/hop |
| $Hopsize_i$ | Hop distance on the UN side. **[INTERP]** The AHD of the UN's nearest anchor, as in traditional DV-HOP | m/hop |
| $h_{ij}$ | Hop count UN *i* → AN *j*. **[INTERP]** The MCR fractional value | hops |

- **[PAPER]** Text: "when calculating the range from UN to AN, the corresponding AN jump distance is taken into account. It takes the median of the two jump distances as the average jump distance" (p. 85530). The median of two values is their mean, so the text and Eq. (11) agree.
- **[INTERP]** A UN has no AHD of its own, so $Hopsize_i$ must be one it received. The most consistent reading is the AHD of its nearest anchor. See Q6.

### 4.5 Intermediate algorithm: HCMCDV-HOP

**[PAPER]** HCMCDV-HOP is §4.1–§4.4 followed by the MLE estimate of Eqs. (5)–(6) (p. 85530: "Finally, the maximum likelihood estimation (MLE) method is utilized to count the final coordinates"). It is a separate curve in Fig. 12.

### 4.6 Improvement 5: linearly-decreasing-weight PSO in place of MLE

**[PAPER] Motivation:** "when using the MLE method … it is easy to encounter the situation of matrix irreversibility" (p. 85530). Classic PSO converges prematurely, so a linearly-decreasing-inertia-weight PSO ("DV-HOP-PSO" / "I-PSO") is used instead (p. 85531).

**Eq. (12), personal best (p. 85530) [PAPER]:**

$$P_i(t+1) = \begin{cases} P_i(t), & \text{if } f(X_i(t+1)) \ge f(P_i(t))\\ X_i(t+1), & \text{if } f(X_i(t+1)) \le f(P_i(t))\end{cases}$$

The two cases overlap at equality. Either choice is harmless.

**Eq. (13), global best [PAPER]:**

$$P_g(t) \in \{P_1(t),\dots,P_N(t)\}\ \big|\ f(P_g(t)) = \min\{f(P_1(t)),\dots,f(P_N(t))\}$$

**Eq. (14), initialisation [PAPER]:**

$$x_{ij}(0) = \mathrm{rdft}()\times(x_{max}-x_{min})+x_{min},\qquad v_{ij}(0) = \mathrm{rdft}()\times v_{max}$$

with $\mathrm{rdft}() \in [0,1]$, $v_{ij}\in[v_{min},v_{max}]$ and $x_{ij}\in[x_{min},x_{max}]$.

**Eq. (15), inertia weight (p. 85531) [PAPER]**, as printed:

$$w = w_s - (w_s - w_e)\,(MaxIt/N)$$

with **$w_s = 0.9$** and **$w_e = 0.4$** [PAPER].

**Eq. (16), objective function [PAPER]**, as printed:

$$f(x,y,z) = \sqrt{\frac{1}{m}\sum_{i=1}^{w}\left(\sqrt{(x-x_i)^2+(y-y_i)^2+(z-z_i)^2} - d_i\right)^2}$$

| Symbol | Meaning | Units |
|---|---|---|
| $X_i(t)$ | Position of particle *i* at iteration *t* (a candidate UN position) | m |
| $P_i(t)$ | Personal best of particle *i* | m |
| $P_g(t)$ | Global best | m |
| $f$ | Objective to minimise. "Root mean square error" (p. 85531) | m |
| $t$ | Iteration index | — |
| $N$ | Population size (Fig. 6: "population size N"). **Clashes** with *N* = number of anchors in Eqs. (1)/(3) | count |
| $D$ | Search-space dimension (Fig. 6). D = 3 for 3D | — |
| $x_{max}, x_{min}$ | Search bounds per dimension | m |
| $v_{max}, v_{min}$ | Velocity bounds | m/iteration |
| $w_s, w_e$ | Initial and final inertia weight: 0.9 and 0.4 | — |
| $MaxIt$ | Maximum iterations ("maxt" in Fig. 6) | count |
| $(x_i,y_i,z_i)$ | Coordinates of anchor *i* | m |
| $d_i$ | Estimated distance UN → anchor *i* (Eq. 11) | m |
| $m$, $w$ (upper sum limit) | **Undefined.** **[INTERP]** Both are the number of anchors used for this UN | count |

Problems:
- **[MISSING] No velocity or position update equation.** The paper gives pbest, gbest, initialisation and the inertia weight, but never $v(t+1) = \dots$ or $x(t+1) = \dots$. **Learning factors $c_1, c_2$ are not given**, although p. 85531 mentions "learning factors". See Q7.
- **[INTERP] Eq. (15) as printed does not decrease.** $MaxIt/N$ contains no iteration counter, so *w* would be constant. With e.g. MaxIt = 100 and N = 30 it would also be negative (0.9 − 0.5·3.33 = −0.77). The text calls it "linear decreasing weights" with *w* going from 0.9 to 0.4, which requires $w(t) = w_s - (w_s - w_e)\,t/MaxIt$. This is almost certainly a typo. See Q8.
- **[INTERP] Eq. (16):** *m* and the upper limit *w* are undefined, and *w* collides with the inertia weight symbol. See Q9.
- **[MISSING]** Population size, MaxIt, $v_{max}$, $v_{min}$ and the search bounds are not given numerically. **[INTERP]** The search bounds are presumably the deployment region, [0, 100] m per axis.
- **[MISSING]** The stopping rule is not given beyond "Iterations < maxt" (Fig. 6).
- **[PAPER]** PSO output: "Outputs $P_g$(Maxt−1) and $f$(Maxt−1)" (Fig. 6).

### 4.7 Complete HCMSPSO-DV-HOP flow (Fig. 7, p. 85531) [PAPER]

1. Initialise the WSN.
2. Anchors propagate their data on multiple communication radii (§4.1).
3. "Constantly correct the jump distance according to the threshold value" (§4.2–4.3).
4. End of broadcast.
5. "Unknown node is an orphan node?" If yes, it is not localised and the flow ends for that node.
6. If no: calculate the distance from each anchor to the unknown node (§4.4, Eq. 11).
7. Calculate the position of nodes to be located using the linear-decreasing-weight PSO (§4.6).
8. Obtain optimal positioning results through continuous iterations.

---

## 5. Anchor-node deployment methodology

- **[PAPER]** Nodes are "randomly distributed" in the 100 m × 100 m × 100 m space (§IV, p. 85531). The paper does not say how anchors are chosen among the nodes.
- **[PAPER]** The anchor ratio ("Anchor Node Scale") is swept from **0.1 to 0.5** in Fig. 12(a).
- **[MISSING]** The probability distribution (uniform or otherwise), the anchor count for experiments other than Fig. 12(a), and whether anchors are a random subset of all nodes are not stated.
- **[PAPER]** Fig. 9(a) shows ≈ 30 anchors (black dots) among the unknown nodes.

## 6. Unknown-node deployment methodology

- **[PAPER]** Same as above: random distribution in the 100 m cube (§IV, p. 85531).
- **[PAPER]** Fig. 9(a) and its text say the distribution "is not uniform". The text gives ranges x ∈ {0, 90}, y ∈ {5, 120}, z ∈ {0, 72} (p. 85532). **Inconsistency:** y up to 120 is outside the stated 100 m region.
- **[MISSING]** No non-uniform distribution model is defined.

## 7. Network dimensions and communication range

| Item | Value | Source | Tag |
|---|---|---|---|
| Deployment region | 100 m × 100 m × 100 m | §IV, p. 85531 | [PAPER] |
| Communication model | A node within CR *R* is a one-hop neighbour (implied by §III-A/B) | pp. 85527, 85529 | [INTERP] (disk/sphere model, not named) |
| CR sweep | 25 → 65 (x-axis of Figs. 12(b), 13; units not labelled, presumably m) | pp. 85533–85534 | [PAPER] / units [INTERP] |
| MCR levels | R/3, 2R/3, R | §III-B, p. 85530 | [PAPER] |
| Default R for non-swept experiments | — | — | [MISSING] |

## 8. Simulation parameters (complete list)

| Parameter | Value | Source | Tag |
|---|---|---|---|
| Simulation tool | MATLAB R2016a, Windows 10 | §IV, p. 85531 | [PAPER] |
| Region | 100 × 100 × 100 m | §IV, p. 85531 | [PAPER] |
| Node placement | "randomly distributed" | §IV, p. 85531 | [PAPER] (distribution [MISSING]) |
| Anchor ratio range | 0.1 – 0.5 | Fig. 12(a) | [PAPER] |
| CR range | 25 – 65 | Figs. 12(b), 13 | [PAPER] |
| Total nodes range | 80 – 240 | Fig. 12(c) | [PAPER] |
| Number of nodes to be located | 30 – 360 | Fig. 14, p. 85535 | [PAPER] |
| Nodes in per-node error plot | ≈ 60 (x-axis 0–60) | Fig. 10 | [PAPER] |
| Test-set nodes in Fig. 9(b) | ≈ 140–150 (x-axis to 140+) | Fig. 9(b) | [PAPER] (read from plot) |
| MCR radii | R/3, 2R/3, R; hop values 1/3, 2/3, 1 | §III-B, p. 85530 | [PAPER] |
| Inertia weight start, $w_s$ | 0.9 | Eq. (15), p. 85531 | [PAPER] |
| Inertia weight end, $w_e$ | 0.4 | Eq. (15), p. 85531 | [PAPER] |
| PSO dimension D | 3 (implied by 3D) | Fig. 6 | [INTERP] |
| Number of repeated tests (Table 1) | 3 ("Test 1–3") | Table 1, p. 85535 | [PAPER] |
| Default total nodes / anchor ratio / R (when not swept) | — | — | [MISSING] |
| Sweep step sizes | — (read approximately from plots only) | Figs. 12–14 | [MISSING] |
| Monte-Carlo repetitions per data point | — | — | [MISSING] |
| PSO population size N | — | — | [MISSING] |
| PSO max iterations | — (Fig. 8 x-axis reaches 300; I-PSO reaches target loss at 172) | Fig. 8 | [MISSING] |
| Learning factors $c_1, c_2$ | — | — | [MISSING] |
| $v_{max}$, $v_{min}$ | — | — | [MISSING] |
| Search bounds $x_{min}$, $x_{max}$ | — (presumably region bounds) | — | [MISSING] |
| Random seed / RNG | — | — | [MISSING] |
| Radio irregularity / noise | none mentioned | — | [INTERP] ideal disk model |

## 9. Experimental methodology (§IV, pp. 85531–85535)

| # | Experiment | Algorithms compared | Varied parameter | Output | Source |
|---|---|---|---|---|---|
| E1 | Optimizer convergence | I-PSO, ACO, chaotic WSA, PSO, DA | Iterations (0–300) | Loss vs iteration; target loss 0.0036 | Fig. 8, pp. 85531–85532 |
| E2 | Error distribution of proposed algorithm | HCMSPSO-DV-HOP | — | 3D node layout and per-node "absolute value of relative error" | Fig. 9, p. 85532 |
| E3 | Per-node positioning error | DV-HOP, GA-DV-HOP, HCMSPSO-DV-HOP | Node number (≈ 60 nodes) | Error (m), Eq. (17) | Fig. 10, p. 85532 |
| E4 | Visual positioning results | DV-HOP, GA-DV-HOP, HCMSPSO-DV-HOP | — | Scatter of estimates with error lines, 2D projection | Fig. 11, p. 85533 |
| E5a | Effect of anchor ratio | DV-HOP, HCMCDV-HOP, HCMCPSO-DV-HOP, 3D-DV-HOP-BEW, Weight GWO DV-HOP | Anchor ratio 0.1–0.5 | Normalised positioning error | Fig. 12(a), p. 85533 |
| E5b | Effect of CR | same five | CR 25–65 | Normalised positioning error | Fig. 12(b) |
| E5c | Effect of total nodes | same five | Total nodes 80–240 | Normalised positioning error | Fig. 12(c) |
| E6 | Terrain types | DV-HOP, HCMCPSO-DV-HOP | CR 25–65 in flat ground, mountain valley, ocean, hillside | Normalised positioning error | Fig. 13, p. 85534 |
| E7 | Accuracy vs number of nodes to locate | Method 1 (proposed) vs Methods 2–5 (Refs. [14], [18], [20], [21]) | Nodes to locate 30–360 | Positioning accuracy (%) | Fig. 14, p. 85535 |
| E8 | Runtime and accuracy, 3 tests | Methods 1–5 | — | Running time (s), PA (%) | Table 1, p. 85535 |

Relevance to this project's scope (traditional 3D DV-HOP vs improved 3D DV-HOP):
- **Can be reproduced for DV-HOP vs HCMSPSO-DV-HOP (and HCMCDV-HOP):** E2, E3, E4, E5a–c, E8 (runtime part).
- **Need comparison algorithms the paper does not specify:** GA-DV-HOP, 3D-DV-HOP-BEW, Weight GWO DV-HOP, ACO, WSA, DA, Methods 2–5. They are only named or cited, never given in implementable detail. They are outside this project's stated scope.
- **E6 terrains:** The four terrain models (flat ground, mountain valley, ocean, hillside) are **never defined** (no height functions, no node constraints). They cannot be reproduced without inventing a model.
- **E1:** "Loss" and the "target loss value" are not defined.

## 10. Performance evaluation metrics

| Metric | Definition in paper | Source | Tag |
|---|---|---|---|
| Positioning error δ | $\delta = \sqrt{(x-x')^2+(y-y')^2}$, **2D only**, no z term | Eq. (17), p. 85532 | [PAPER]; 2D form in a 3D paper is [INTERP] probable omission |
| Normalised positioning error | "other experiments use errors represented by normalized positioning errors", with **no formula** | p. 85532; Figs. 12, 13 | [MISSING] |
| Absolute value of relative error | Used in Fig. 9(b), with **no formula** | p. 85532 | [MISSING] |
| Positioning accuracy (%) | Used in Fig. 14 and Table 1, with **no formula** | p. 85535 | [MISSING] |
| Running time (s) | ART over 3 tests. What is timed (whole network or per node, and on which hardware) is not stated | Table 1 | [PAPER] / scope [MISSING] |
| Iteration loss | Fig. 8, undefined | p. 85531 | [MISSING] |

Symbols in Eq. (17): $(x, y)$ is the true UN position and $(x', y')$ the estimate, both in m. δ is in m.

## 11. Graphs and tables in the paper

| Item | Content | Page |
|---|---|---|
| Fig. 1 | WSN structure (illustration) | 85527 |
| Fig. 2 | Sensor node hardware structure (illustration) | 85527 |
| Fig. 3 | 2D and 3D DV-HOP positioning models (illustration) | 85528 |
| Fig. 4 | 3D DV-HOP flowchart | 85528 |
| Fig. 5 | Single vs three communication radii (3D illustration) | 85529 |
| Fig. 6 | PSO flowchart and particle-motion diagram | 85530 |
| Fig. 7 | HCMSPSO-DV-HOP flowchart | 85531 |
| Fig. 8 | Loss vs iterations, 5 optimizers | 85531 |
| Fig. 9 | (a) 3D node distribution; (b) per-node absolute relative error | 85532 |
| Fig. 10 | Per-node error (m) for DV-HOP, GA-DV-HOP, HCMSPSO-DV-HOP | 85532 |
| Fig. 11 | Estimated-vs-true scatter (2D, 100 × 100 m) for 3 algorithms plus the real distribution | 85533 |
| Fig. 12 | Normalised error vs (a) anchor ratio, (b) CR, (c) total nodes, 5 algorithms | 85533 |
| Fig. 13 | Normalised error vs CR in 4 terrains, DV-HOP vs improved | 85534 |
| Fig. 14 | PA (%) vs number of nodes to locate, 5 methods | 85535 |
| Table 1 | Running time and PA for 5 methods across 3 tests | 85535 |

## 12. Reported experimental observations (numbers as reported)

- **Fig. 8:** I-PSO reaches target loss 0.0036 in 172 iterations. ACO takes 288, WSA 232, PSO 246, DA 229 (pp. 85531–85532).
- **Fig. 9:** Errors mostly between 0.00 and 0.15. Mean absolute relative error **0.048** (p. 85532).
- **Fig. 10:** Error ranges: DV-HOP 2.16–3.62, GA-DV-HOP 1.89–3.25, HCMSPSO-DV-HOP **1.62–2.51** (p. 85532; y-axis "Error (m)").
- **Fig. 12(a):** Error falls as anchor ratio grows. HCMCPSO-DV-HOP mean error **0.12** (p. 85533). Read from the plot: DV-HOP ≈ 0.48 → 0.30, HCMCDV-HOP ≈ 0.32 → 0.20, HCMCPSO ≈ 0.23 → 0.15.
- **Fig. 12(b):** Error falls as CR grows. HCMCPSO varies least (p. 85534).
- **Fig. 12(c):** Error falls as total nodes grow. HCMCPSO mean error **0.09** (p. 85534).
- **Fig. 13:** Improved algorithm roughly equal across terrains ("variation amplitude of no more than 0.02"). DV-HOP mean **0.56** vs improved **0.12**, a reduction of 0.44 (p. 85534).
- **Fig. 14:** Method 1: 98.7% at 30 nodes, 94.4% at 360, mean 96.8%, a drop of 4.2% (p. 85535).
- **Table 1:** Method 1 ART **0.49 s**, mean PA **96.40%**. Per test: 0.48/96.42, 0.51/96.43, 0.49/96.36 (p. 85535).

## 13. Internal inconsistencies observed in the paper

1. Two names for the proposed method: HCMSPSO vs HCMCPSO.
2. Eq. (9) summand index typo ($c_{ij}$ instead of $c_{il}$).
3. Eq. (15) has no iteration variable, so *w* does not decrease (§4.6).
4. Eq. (16): undefined *m*, and *w* reused as a sum limit.
5. Eq. (17) is 2D in a 3D study.
6. The PSO velocity/position update is missing entirely.
7. Fig. 9 text gives y ∈ {5, 120}, outside the 100 m region.
8. The text refers to "Figure 10 (b)" and "Figure 10 (c)" when describing Fig. 11(b)/(c) (p. 85532).
9. Fig. 11 plots are 2D (100 × 100) for a 3D experiment.
10. Fig. 13 text: "the PA of the improved DHA is the highest" in flat terrain, yet the "variation amplitude [is] no more than 0.02" while the plotted improved curves span about 0.2. The reported DV-HOP mean of 0.56 is not consistent with panel (a), whose values are ≈ 0.2–0.38.
11. Abstract mean PA is 96.40% (Table 1), but the Fig. 14 text gives 96.8%. These come from different experiments, so this is not necessarily an error.
12. Symbol *N* means number of anchors in Eqs. (1)/(3) and population size in Eq. (13) and Fig. 6.

## 14. Limitations and assumptions (stated or implied by the paper)

- **[PAPER]** Only static nodes. Mobility is left for future work (§V, p. 85535).
- **[PAPER]** Time complexity and data volume need further reduction (§V).
- **[INTERP]** An ideal spherical (unit-disk) radio model. No path loss, fading, irregularity or packet loss is modelled.
- **[INTERP]** Hop threshold and weights (Eqs. 7–8) use anchors' **true** positions, which is legitimate because anchors know their coordinates.
- **[INTERP]** MCR assumes anchors (possibly all nodes, see Q1) can transmit at three power levels. This costs energy, which the paper does not evaluate.
- **[PAPER]** Orphan/isolated nodes cannot be located (Figs. 4, 7).
- **[MISSING]** No statistical reporting: no confidence intervals, no number of Monte-Carlo runs, no seeds.
- **[MISSING]** Many parameters needed for exact reproduction are absent (§8). Exact numerical reproduction is therefore impossible. Only methodology and trends can be compared.
