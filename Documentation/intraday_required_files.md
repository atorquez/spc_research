
---

# 📘 **required_files.md**

```md
# Required Files for Page 11 — Intraday Ranker

Page 11 depends on exactly **five files** inside the `spc_research_v2` project.  
These files form the complete dependency chain for the Intraday Readiness Model.

---

## 1. `pages/11_Intraday_Ranker.py`
The Streamlit page responsible for:
- UI
- filters
- cluster selection
- universe building
- calling `rank_universe()`
- displaying results

This is the front-end of the intraday ranker.

---

## 2. `analysis/intraday_ranker.py`
The main model engine containing:
- fetch_daily
- calculate_indicators
- compute_pca_components
- VMAS
- BuyZone Heatmap
- Buy_Signal
- rank_universe

This is the core logic used by Page 11.

---

## 3. `analysis/under_control_explorer.py`
Provides:
- `intraday_buy_zone()`
- PCA preprocessing indicators
- daily indicator logic

Page 11 imports:
```python
from analysis.under_control_explorer import intraday_buy_zone

