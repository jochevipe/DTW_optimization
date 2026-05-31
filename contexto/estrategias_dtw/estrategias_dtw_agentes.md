# DTW Adaptation Strategies — Agent Technical Reference

> This document is for AI agents implementing or modifying adaptation strategies
> in this project. It contains precise specifications: file paths, interfaces,
> data shapes, and pseudocode. Read this before writing any code.

---

## 1. Architecture Overview

```
StagnationMonitor  →  Strategy Layer (decision)  →  MH.adapt()
     (sensor)              (brain)                   (actuator)
```

- **StagnationMonitor** (`mkp_common/monitor.py`): Produces raw DTW metrics. NEVER MODIFY THIS for strategy changes.
- **Strategy Layer** (`fire_binario/runner.py`): Currently hardcoded as `mh.adapt(out["fire"])`. This is what changes per strategy.
- **MH.adapt()** (`mkp_common/base.py` + each MH): Receives the decision and adjusts parameters.

---

## 2. Monitor Output Shape

`StagnationMonitor.update(new_best: float) -> dict` returns:

### Before warm-up (iteration < window):
```python
{
    "ready": False,
    "fire": False,
    "no_improve_len": int,  # consecutive iterations without improvement
    "n": int,               # total observations so far
}
```

### After warm-up (iteration >= window):
```python
{
    "ready": True,
    "fire": bool,              # current fire decision (3-condition logic)
    "D1_vs_ramp": float,       # DTW distance to ideal ramp (progress)
    "D2_vs_const": float,      # DTW distance to plateau (stagnation)
    "delta": float,            # D1 - D2
    "theta_c": float,          # adaptive threshold for D2 (percentile p_low of D2 history)
    "theta_r": float,          # adaptive threshold for D1 (percentile p_high of D1 history)
    "theta_delta": float,      # adaptive threshold for delta (percentile p_high of delta history)
    "no_improve_len": int,     # consecutive iterations without improvement
    "trigger_streak": int,     # consecutive iterations where all 3 conditions hold
    "n": int,                  # total observations
}
```

### Metric semantics

| Metric | Low value means | High value means |
|--------|----------------|-----------------|
| `D1_vs_ramp` | Fitness curve resembles ideal ramp → MH is **progressing** | Fitness curve is far from ramp → MH is **not progressing** |
| `D2_vs_const` | Fitness curve resembles plateau → MH is **stagnated** | Fitness curve has activity → MH is **not stagnated** |
| `delta` | Negative → closer to ramp than plateau → **progress** | Positive → closer to plateau than ramp → **stagnation** |
| `theta_c` | N/A (reference) | N/A. It's the p_low percentile of D2 history. D2 <= theta_c means "flatter than usual" |
| `theta_r` | N/A (reference) | N/A. It's the p_high percentile of D1 history. D1 >= theta_r means "worse progress than usual" |
| `theta_delta` | N/A (reference) | N/A. It's the p_high percentile of delta history. delta >= theta_delta means "more stagnated than usual" |

### Normalized ratios (construct these from raw metrics)

```python
eps = 1e-10

r_stagnation = D2 / (theta_c + eps)
# < 1 → curve is flatter than historical norm → stagnated
# > 1 → curve has more activity than norm → not stagnated

r_progress = D1 / (theta_r + eps)
# < 1 → better progress than historical norm
# > 1 → worse progress than historical norm

r_balance = delta / (theta_delta + eps)
# < 0 → net progress
# 0 to 1 → mild to moderate stagnation
# > 1 → severe stagnation (worse than 70th percentile of history)
```

---

## 3. Current MH Interface

### BaseMH (abstract class at `mkp_common/base.py`)

```python
class BaseMH(ABC):
    mode: str  # "exploit" or "explore" — always starts as "exploit"

    def initialize(self) -> None: ...
    def step(self) -> float: ...                # returns gbest_fitness
    def adapt(self, fire: bool) -> None: ...    # switches mode + params
    def get_best(self) -> Tuple[np.ndarray, float]: ...
```

### Per-MH parameter sets (exploit → explore)

| MH | File | Parameters | Exploit values | Explore values |
|----|------|-----------|----------------|----------------|
| BinaryPSO | `mkp_common/mh/pso.py` | w, c1, c2 | 0.729, 1.49445, 1.49445 | 0.9, 2.5, 0.5 |
| GA | `mkp_common/mh/ga.py` | crossover_rate, mutation_rate | 0.9, 0.01 | 0.6, 0.15 |
| GWO | `mkp_common/mh/gwo.py` | a | 0.5 | 2.0 |
| DE | `mkp_common/mh/de.py` | F, CR | 0.5, 0.9 | 0.9, 0.3 |

### Current adapt() pattern (identical in all 4 MHs):
```python
def adapt(self, fire: bool) -> None:
    if fire and self.mode != "explore":
        self.mode = "explore"
        # set all params to EXPLORE values
    elif not fire and self.mode == "explore":
        self.mode = "exploit"
        # set all params to EXPLOIT values
```

---

## 4. Runner Integration Point

File: `fire_binario/runner.py`, function `run_experiment()`.

The decision point is at line ~57-58:
```python
out = monitor.update(fitness)
# ...
if out.get("ready"):
    mh.adapt(out["fire"])  # <— THIS IS WHAT CHANGES PER STRATEGY
```

For boolean strategies: replace `out["fire"]` with custom logic using `out` fields.
For continuous strategies: replace `mh.adapt(out["fire"])` with `mh.adapt_continuous(intensity)`.

---

## 5. Strategy Specifications

### Family A: Boolean (discrete fire/no-fire)

All Family A strategies keep `adapt(fire: bool)` unchanged. Only the fire calculation changes.

---

#### A1 — Delta Pure

```python
fire = out["delta"] > 0
```

- Uses: `delta` only
- No hypers beyond DTW config
- Expected: very noisy, frequent oscillation between modes

---

#### A2 — Delta + Theta

```python
fire = out["delta"] >= out["theta_delta"]
```

- Uses: `delta`, `theta_delta`
- Auto-normalized: fires only when stagnation is worse than historical 70th percentile
- No patience, no plateau check

---

#### A3 — D2 Pure

```python
fire = out["D2_vs_const"] <= out["theta_c"]
```

- Uses: `D2_vs_const`, `theta_c`
- Direct stagnation check: "is the curve flat?"
- Ignores progress signal entirely

---

#### A4 — Current Baseline (3 conditions + patience)

This is what `StagnationMonitor.update()` already computes as `out["fire"]`.

```python
cond_plateau  = out["no_improve_len"] >= cfg.plateau_max
cond_constant = out["D2_vs_const"] <= out["theta_c"]
cond_ramp     = (out["D1_vs_ramp"] >= out["theta_r"]) or (out["delta"] >= out["theta_delta"])

# Internal to monitor: trigger_streak increments when all 3 are True
fire = out["trigger_streak"] >= cfg.patience
```

- Uses: all 6 DTW params + no_improve_len + plateau_max + patience
- Most conservative, best anti-noise filtering

---

#### A5 — Normalized Ratio + Patience

```python
eps = 1e-10
r_balance = out["delta"] / (out["theta_delta"] + eps)

# Maintain external streak counter (not in monitor)
if r_balance > 1.0:
    streak += 1
else:
    streak = 0

fire = streak >= patience
```

- Uses: `delta`, `theta_delta`, external `patience`
- Simpler than A4 but with temporal smoothing
- Requires external streak counter in runner

---

### Family B: Continuous (intensity ∈ [0, 1])

Family B strategies require a new method in BaseMH and all 4 MH implementations.

#### Required interface change in `mkp_common/base.py`:

```python
class BaseMH(ABC):
    # ... existing methods ...

    def adapt_continuous(self, intensity: float) -> None:
        """
        Adapt parameters on a continuous scale.
        intensity = 0.0 → pure exploit parameters
        intensity = 1.0 → pure explore parameters
        intensity between → linear interpolation
        """
        ...
```

#### Required implementation pattern (example for PSO):

```python
def adapt_continuous(self, intensity: float) -> None:
    intensity = max(0.0, min(1.0, intensity))  # clamp [0, 1]

    self.w  = self.W_EXPLOIT  + intensity * (self.W_EXPLORE  - self.W_EXPLOIT)
    self.c1 = self.C1_EXPLOIT + intensity * (self.C1_EXPLORE - self.C1_EXPLOIT)
    self.c2 = self.C2_EXPLOIT + intensity * (self.C2_EXPLORE - self.C2_EXPLOIT)

    # Update mode label for logging
    if intensity > 0.5:
        self.mode = "explore"
    else:
        self.mode = "exploit"
```

#### Required implementation pattern (example for GWO — single param):

```python
def adapt_continuous(self, intensity: float) -> None:
    intensity = max(0.0, min(1.0, intensity))
    self.a = self.A_EXPLOIT + intensity * (self.A_EXPLORE - self.A_EXPLOIT)
    self.mode = "explore" if intensity > 0.5 else "exploit"
```

#### Required implementation pattern (example for GA):

```python
def adapt_continuous(self, intensity: float) -> None:
    intensity = max(0.0, min(1.0, intensity))
    self.crossover_rate = self.CX_EXPLOIT + intensity * (self.CX_EXPLORE - self.CX_EXPLOIT)
    self.mutation_rate  = self.MUT_EXPLOIT + intensity * (self.MUT_EXPLORE - self.MUT_EXPLOIT)
    self.mode = "explore" if intensity > 0.5 else "exploit"
```

#### Required implementation pattern (example for DE):

```python
def adapt_continuous(self, intensity: float) -> None:
    intensity = max(0.0, min(1.0, intensity))
    self.F  = self.F_EXPLOIT  + intensity * (self.F_EXPLORE  - self.F_EXPLOIT)
    self.CR = self.CR_EXPLOIT + intensity * (self.CR_EXPLORE - self.CR_EXPLOIT)
    self.mode = "explore" if intensity > 0.5 else "exploit"
```

---

#### B1 — Sigmoid on Normalized Delta

```python
import math

eps = 1e-10
k = 5.0       # steepness (higher = sharper transition)
center = 0.5  # inflection point on r_balance scale

raw = out["delta"] / (out["theta_delta"] + eps)
intensity = 1.0 / (1.0 + math.exp(-k * (raw - center)))
mh.adapt_continuous(intensity)
```

- Uses: `delta`, `theta_delta`
- Hypers: `k` (steepness), `center` (inflection point)
- When delta/theta_delta << center → intensity ≈ 0 (exploit)
- When delta/theta_delta >> center → intensity ≈ 1 (explore)
- Smooth transition, no oscillation

---

#### B2 — Dual Sigmoid (D1 + D2 independent)

```python
import math

eps = 1e-10
k1 = 5.0    # steepness for progress signal
k2 = 5.0    # steepness for stagnation signal
alpha = 0.5 # weight: 0 = only stagnation, 1 = only progress

r_prog = out["D1_vs_ramp"] / (out["theta_r"] + eps)
r_stag = out["D2_vs_const"] / (out["theta_c"] + eps)

s_progress   = 1.0 / (1.0 + math.exp(-k1 * (r_prog - 1.0)))
s_stagnation = 1.0 / (1.0 + math.exp(-k2 * (1.0 - r_stag)))

intensity = alpha * s_progress + (1.0 - alpha) * s_stagnation
intensity = max(0.0, min(1.0, intensity))
mh.adapt_continuous(intensity)
```

- Uses: `D1_vs_ramp`, `D2_vs_const`, `theta_r`, `theta_c`
- Hypers: `k1`, `k2`, `alpha`
- Most expressive: separates progress and stagnation signals
- Higher complexity, harder to calibrate

---

#### B3 — Inverted D2 as Intensity

```python
eps = 1e-10
scale = 2.0  # how many multiples of theta_c maps to intensity=0

ratio = out["D2_vs_const"] / (out["theta_c"] * scale + eps)
intensity = 1.0 - max(0.0, min(1.0, ratio))
mh.adapt_continuous(intensity)
```

- Uses: `D2_vs_const`, `theta_c`
- Hypers: `scale`
- D2 low (flat/stagnated) → ratio small → intensity high → explore
- D2 high (active) → ratio large → intensity low → exploit
- Simplest continuous strategy

---

## 6. Runner Modification Pattern

### For a boolean strategy (Family A):

```python
# In run_experiment(), replace the decision block:
out = monitor.update(fitness)
if out.get("ready"):
    # --- Strategy A2 example ---
    fire = out["delta"] >= out["theta_delta"]
    mh.adapt(fire)
```

### For a continuous strategy (Family B):

```python
# In run_experiment(), replace the decision block:
import math

out = monitor.update(fitness)
if out.get("ready"):
    # --- Strategy B1 example ---
    eps = 1e-10
    k, center = 5.0, 0.5
    raw = out["delta"] / (out["theta_delta"] + eps)
    intensity = 1.0 / (1.0 + math.exp(-k * (raw - center)))
    mh.adapt_continuous(intensity)
```

### Historial logging for continuous strategies:

The `historial_modos` list currently stores `"exploit"` or `"explore"`. For continuous
strategies, also store the intensity value for plotting:

```python
historial_modos.append(mh.mode)
historial_intensity.append(intensity)  # new list, float values [0, 1]
```

---

## 7. File Modification Checklist

### To implement any Family A strategy:
- [ ] Modify `fire_binario/runner.py` → change fire calculation in `run_experiment()`
- [ ] (Optional) Add strategy config to `fire_binario/config.py`
- [ ] No changes needed in `mkp_common/` (monitor, base, MHs stay the same)

### To implement any Family B strategy:
- [ ] Add `adapt_continuous(intensity: float)` to `mkp_common/base.py`
- [ ] Implement `adapt_continuous()` in all 4 MHs: `pso.py`, `ga.py`, `gwo.py`, `de.py`
- [ ] Modify `fire_binario/runner.py` → compute intensity, call `adapt_continuous()`
- [ ] Add `historial_intensity` to result dict in `run_experiment()`
- [ ] Update `fire_binario/run.py` plots to show intensity curve
- [ ] Update `fire_binario/resultados.py` comparison plots for intensity data
- [ ] Add strategy config (k, center, scale, etc.) to `fire_binario/config.py`

---

## 8. Testing / Validation Notes

- All strategies should be tested on the same instance (default: `mknapcb1.txt`, index 0)
  with the same seeds (epochs 1-10) to ensure fair comparison.
- Monitor `fire_count` across strategies to verify behavior differences.
- For Family B, verify that `intensity` values actually span the [0, 1] range and
  don't saturate at 0 or 1 constantly (which would mean the sigmoid params are wrong).
- The current config is at `fire_binario/config.py` with defaults:
  `window=20, patience=2, plateau_max=10, min_slope=2.0, use_ddtw=True, band=2`.
