[README (1).md](https://github.com/user-attachments/files/25728641/README.1.md)
# Optimal Weighting of GDP and GDI for Productivity Measurement
### A Signal Extraction Approach

**Author:** Lamae A. Maharaj  
**Date:** February 2026

---

## Overview

GDP and GDI measure the same underlying economic activity from opposite sides of the national accounts, yet they routinely diverge due to independent measurement error. Standard practice either relies on GDP alone or applies the BEA's ad hoc 50–50 average — neither of which uses available information on the relative measurement quality of each series.

This project derives an **optimal weighted combination** of GDP and GDI using a signal extraction framework. Weights are determined by the relative revision volatility of each series, estimated from FRED real-time vintage data over 1990–2024. The optimal output measure is then used to construct an alternative labor productivity series, which is compared against the GDP-based and BLS official measures.

---

## Key Findings

- GDI exhibits slightly lower revision volatility than GDP over the sample period (σ = 1.894 vs 1.961 percentage points), implying the optimal measure tilts modestly toward GDI.
- The estimated optimal weights are **47.4% GDP and 52.6% GDI**, close to but distinct from the BEA 50–50 average.
- When translated into labor productivity growth, the optimal series tracks the GDP-based measure closely on average, with a mean difference of approximately **0.008 percentage points**.
- The largest divergences occur during episodes of large GDP–GDI discrepancies: the dot-com contraction (1999–2001) and the early COVID quarters (2020).
- The 50–50 average performs reasonably well as a practical approximation but revision-based weighting provides a more defensible benchmark when measurement quality differs across the two output concepts.

---

## Methodology

### Signal Extraction Framework

Let true output $Y_t^*$ be observed with error:

$$GDP_t = Y_t^* + u_t, \quad GDI_t = Y_t^* + v_t$$

where $u_t$ and $v_t$ are measurement errors with standard deviations $\sigma_u$ and $\sigma_v$ and correlation $\rho$. The minimum-variance linear combination places weight $\lambda$ on GDP:

$$\hat{Y}_t = \lambda \cdot GDP_t + (1 - \lambda) \cdot GDI_t$$

The optimal $\lambda$ is:

$$\lambda^* = \frac{\sigma_v^2 - \rho \sigma_u \sigma_v}{\sigma_u^2 + \sigma_v^2 - 2\rho \sigma_u \sigma_v}$$

### Estimating Measurement Error

Revision standard deviations are estimated from FRED real-time vintage data. For each quarter, the revision is defined as the difference between the final reported annualized log growth rate and the initial estimate:

$$\text{revision}_t = \Delta \ln(GDP_t^{\text{final}}) - \Delta \ln(GDP_t^{\text{initial}})$$

### Productivity Growth

Labor productivity is output per hour, with growth computed as the annualized log change:

$$\Delta \ln(LP_t) = 400 \cdot \ln\left(\frac{LP_t}{LP_{t-1}}\right)$$

The factor of 400 = 4 × 100 annualizes the quarterly log difference (×4) and converts from decimal to percentage points (×100).

---

## Results

### Parameter Estimates

| Parameter | Estimate |
|---|---|
| σ\_GDP (revision std. dev., pp) | 1.961 |
| σ\_GDI (revision std. dev., pp) | 1.894 |
| ρ (correlation of revisions) | 0.316 |
| λ (optimal weight on GDP) | 0.474 |
| Weight on GDP (%) | 47.43 |
| Weight on GDI (%) | 52.57 |

### Summary Statistics — Annualized Productivity Growth (%)

| Series | Mean | Std. Dev. |
|---|---|---|
| GDP-based | 3.91 | 2.89 |
| BEA 50–50 | 3.92 | 2.66 |
| Optimal | 3.92 | 2.66 |
| BLS official | 2.00 | 3.08 |

### Subperiod Comparison

| Period | GDP-based | Optimal | Diff. | N |
|---|---|---|---|---|
| Pre-crisis (1990–2007) | 4.21 | 4.22 | +0.016 | 71 |
| Financial crisis (2008–2009) | 5.32 | 5.44 | +0.117 | 8 |
| Recovery (2010–2019) | 2.21 | 2.22 | +0.010 | 40 |
| COVID era (2020–2024) | 5.60 | 5.57 | −0.027 | 20 |

---

## Data Sources

| Series | Source | FRED ID |
|---|---|---|
| GDP (real-time vintages) | Bureau of Economic Analysis via FRED | `GDP` |
| GDI (real-time vintages) | Bureau of Economic Analysis via FRED | `GDI` |
| Nonfarm business output per hour | Bureau of Labor Statistics via FRED | `OPHNFB` |
| Nonfarm business hours | Bureau of Labor Statistics via FRED | `HOANBS` |

All data retrieved via the FRED API using real-time vintage releases from 1990 onward.

---

## Repository Structure

```
├── analysis.py                  # Main analysis script
├── main.tex                     # LaTeX paper (results section + title page)
├── data/
│   ├── parameter_estimates.csv  # Estimated σ, ρ, and λ
│   ├── summary_statistics.csv   # Mean and std. dev. by series
│   └── subperiod_comparison.csv # Subperiod averages
├── figures/
│   ├── productivity_comparison.png   # Figure 1: four series over time
│   └── productivity_difference.png   # Figure 2: optimal minus GDP-based
└── README.md
```

---

## Requirements

```
pandas
numpy
matplotlib
seaborn
fredapi
```

Install with:

```bash
pip install pandas numpy matplotlib seaborn fredapi
```

A FRED API key is required. Register for one at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html) and set it in the script:

```python
fred = Fred(api_key="your_api_key_here")
```

---

## Running the Analysis

```bash
python analysis.py
```

The script downloads data directly from FRED, computes revision statistics, estimates optimal weights, constructs productivity series, and saves all outputs to the `data/` and `figures/` directories.

---

## Reference

Nalewaik, J. (2010). The income- and expenditure-side estimates of U.S. output growth. *Brookings Papers on Economic Activity*, 71–106.
