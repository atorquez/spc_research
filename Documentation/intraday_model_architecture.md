# SPC Intraday Readiness Model — Architecture Diagram

Below is the full architecture diagram describing how the model processes data, computes signals, and produces actionable classifications.

┌──────────────────────────────────────────┐
│      SPC Intraday Readiness Model        │
└──────────────────────────────────────────┘
│
▼
┌────────────────────────────────────────────────────────────┐
│                  STAGE 1 — DAILY STRUCTURE                 │
└────────────────────────────────────────────────────────────┘
│
┌──────────────────────────────────────────────────────────────────────┐
│ Inputs: 3 months of daily OHLCV data                                 │
│                                                                      │
│ • Trend Structure (EMA9, EMA20, EMA50)                               │
│ • Volatility (ATR%)                                                  │
│ • Participation (RVOL)                                               │
│ • Opening Pressure (Gap%)                                            │
│ • Value Zones (BuyZone10, BuyZone5 via rolling percentiles)          │
└──────────────────────────────────────────────────────────────────────┘
│
▼
┌────────────────────────────────────────────────────────────┐
│             STAGE 2 — INTRADAY PCA ENGINE                  │
└────────────────────────────────────────────────────────────┘
│
┌──────────────────────────────────────────────────────────────────────┐
│ Inputs: Intraday-sensitive indicators                                │
│                                                                      │
│ • RSI                                                                 │
│ • Bollinger Band Width                                                │
│ • Rate of Change (ROC)                                                │
│ • Stochastic %K                                                       │
│ • EMA Curvature                                                       │
│ • Volume Delta                                                        │
│ • VWAP Distance                                                       │
│                                                                      │
│ Process: StandardScaler → PCA(n=3)                                   │
│                                                                      │
│ Outputs: PCA1 (Momentum), PCA2 (Volatility), PCA3 (Participation)    │
└──────────────────────────────────────────────────────────────────────┘
│
▼
┌────────────────────────────────────────────────────────────┐
│                 STAGE 3 — VALUE–MOMENTUM FUSION            │
└────────────────────────────────────────────────────────────┘
│
┌──────────────────────────────────────────────────────────────────────┐
│ • VMAS = Value–Momentum Alignment Score                              │
│ • BuyZone Heatmap (Inside_5, Inside_10, Near_Value, Normal, Extended)│
│ • Distance from BuyZone10/5                                          │
└──────────────────────────────────────────────────────────────────────┘
│
▼
┌────────────────────────────────────────────────────────────┐
│                 STAGE 4 — BUY SIGNAL ENGINE                │
└────────────────────────────────────────────────────────────┘
│
┌──────────────────────────────────────────────────────────────────────┐
│ Combines:                                                            │
│ • Trend (EMA alignment)                                              │
│ • Value proximity (BuyZone10/5)                                      │
│ • Momentum (PCA1)                                                    │
│ • VMAS                                                               │
│ • Heatmap classification                                             │
│                                                                      │
│ Output:                                                              │
│ • Strong Buy Zone                                                    │
│ • Buy Zone                                                           │
│ • Neutral                                                            │
│ • Avoid                                                              │
│ • Extended                                                           │
└──────────────────────────────────────────────────────────────────────┘
│
▼
┌────────────────────────────────────────────────────────────┐
│                 STAGE 5 — TRADER CONFIRMATION              │
└────────────────────────────────────────────────────────────┘
│
┌──────────────────────────────────────────────────────────────────────┐
│ Trader visually confirms timing using:                               │
│ • EMA9 reclaim                                                        │
│ • RSI > 50                                                            │
│ • PCA1 slope                                                          │
│ • RVOL trend                                                          │
│ • Higher-low formation                                                │
└──────────────────────────────────────────────────────────────────────┘
