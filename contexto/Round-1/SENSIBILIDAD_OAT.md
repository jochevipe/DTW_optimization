# OAT sensitivity analysis for the DTW revision

## Purpose

The revision response needs evidence that the DTW monitor is not dependent on
one narrowly tuned parameter combination. This experiment uses **one-factor-at-a-time
(OAT)** sensitivity analysis: one monitor parameter is changed while all other
parameters remain at the paper values.

OAT is preferred here to an automatic tuner such as irace or SMAC because the
review response needs an interpretable ablation of the design choices, not a
new optimized configuration. Each result can therefore be described directly
as “this parameter was changed while the other six were held fixed”. An
automatic tuner would introduce a second optimization problem and would make
it harder to attribute an observed change to a particular parameter.

## Experimental design

- **Strategy:** Binary-Complex only.
- **Instances:** `mknapcb1[0, 15, 29]` (indices in `instances/mknapcb1.txt`).
- **Metaheuristics:** PSO, GA, GWO, and DE.
- **Epochs:** 31 per configuration, instance index, and metaheuristic.
- **Configurations:** 1 paper base configuration plus 3 off-base values for
  each of 7 parameters, for **22 configurations** total.
- **Execution:** every run receives all seven environment variables explicitly;
  the base configuration is therefore independent of the local configuration
  defaults.

The grid is:

| Parameter | Values (paper value marked `*`) |
|---|---|
| `window` | 50, 100, 200*, 400 |
| `band` | 1, 2*, 4, 8 |
| `min_slope` | 1.0, 2.0*, 3.0, 4.0 |
| `p_low` | 20.0, 30.0, 40.0*, 50.0 |
| `p_high` | 50.0, 60.0*, 70.0, 80.0 |
| `plateau_max` | 3, 5*, 8, 12 |
| `patience` | 1, 2, 3*, 5 |

The per-configuration campaign identifier is recorded in `configs.json`, so
runs from different OAT configurations cannot overwrite one another. The
analysis aggregates the serialized per-epoch `fitness` values over the three
selected indices and all available epochs.

## Commands

Run the campaign from the project root (the command is intentionally not part
of routine short verification because it is a long HPC campaign):

```bash
python -m sensibilidad.run_sensitivity --cpus 40 --epochs 31
```

Resume an interrupted campaign (e.g. SLURM time limit) reusing the same
manifest and per-configuration campaign ids, so the base configuration of the
original campaign remains comparable:

```bash
python -m sensibilidad.run_sensitivity --campaign <id> --cpus 40 --epochs 31
```

Without filters, resume runs only incomplete configurations (each
configuration is considered complete when its four MH JSON files exist for
every selected index). `--desde-config <id>` and `--solo <id>` override that
selection.

After the campaign completes, analyze a campaign directory by its timestamp:

```bash
python -m sensibilidad.analizar --campaign <id>
```

The analysis writes `tabla_oat.md` under
`results/sensibilidad/campaign_<id>/` and also prints the tables to stdout.

## Planned use in the revision response

The resulting tables will support the following reviewer-response points:

- **R1.4:** document sensitivity of the DTW monitor parameters and show that
  the paper choice is not an unexplained isolated setting.
- **R2.3:** provide the OAT ablation evidence for the Binary-Complex strategy.
- **R3.5:** report the robustness/tuning procedure and the selected paper base
  values transparently.
