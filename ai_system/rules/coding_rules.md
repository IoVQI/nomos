---
project_version: "0.9.0"
document_version: "1.4"
language: "en"
last_updated: "2026-10-20"
category: "ai_rules"
tags: [coding, style, python, reproducibility]
---

# Scientific Coding Rules

> A generic baseline for scientific code. It encodes conventions that are easy to state,
> hard to remember, and expensive to discover late: units, validation gates, reproducibility,
> and the difference between a passing test and a correct result.
>
> Adopters should keep the structure and replace the domain-specific examples with their own.

---

# General Style

Preferred language:
- Python

Preferred libraries:
- numpy
- scipy
- matplotlib

Optional:
- numba
- h5py
- pandas

---

# Code Structure

Prefer:
- modular functions
- small reusable components
- explicit variable names

Avoid:
- deeply nested logic
- hidden state
- excessive globals

---

# Documentation

Every public function must include:
- purpose
- parameters
- units
- return values

Example:

```python
def pressure(density):
    """
    Compute pressure from density.

    Parameters
    ----------
    density : float
        Density [g/cm^3]

    Returns
    -------
    pressure : float
        Pressure [dyn/cm^2]
    """
```

---

# Units and Conventions

| Rule | Requirement |
|------|-------------|
| **One internal unit system** | Pick natural or SI/CGS for internal computation and state it in one place |
| **Convert at boundaries** | Convert to the output unit system only in a dedicated export function |
| **No hidden conversions** | Never multiply by a unit factor inline without an annotation |
| **Constants from one source** | Import physical constants from a single module, not per-file literals |

```python
# Correct: internal = one system, output = explicit conversion
energy_internal = compute_energy(density, params)
pressure_internal = compute_pressure(density, params)
export_with_units(energy_internal, pressure_internal, output_path)

# Wrong: mixing systems without annotation
rho_cgs = density * 1.67e-24       # hidden conversion
pressure_cgs = pressure_internal * 1.602e33
```

---

# Validation Gates

Before a result is consumed downstream, it must pass the domain's validation gate.
A gate should check the invariants that make the result physically/statistically meaningful:

- boundedness (e.g. a quantity that must lie in `[0, 1]`);
- monotonicity where the model requires it;
- positivity where required;
- conservation laws;
- agreement with an independent reference at a fiducial point.

```python
def produce(params, grid):
    result = compute(params, grid)
    validate(result)          # raises on failure; blocks downstream
    return result
```

> **A passing gate is not proof of correctness.** It only says the declared invariants hold.
> Conclusions still need an independent check (see `standards/10`).

---

# Regression Tests

At least one fiducial point must be verified against a known reference:

```python
def test_fiducial():
    """Verify the model at a canonical input against a reference value."""
    x0 = 0.16
    result = produce(default_params, np.array([x0]))
    assert result["x"].iloc[0] == pytest.approx(x0, rel=1e-6)
    assert result["y"].iloc[0] == pytest.approx(ref_y, rel=1e-4)
```

Reference values may come from:
(a) the original paper's table/figure,
(b) a previously verified baseline,
(c) an independent implementation at a canonical point.

### Convention-change backfill

When a convention changes (units, factors, definitions), the change is not complete until
every artifact encoding the **old expectation** is backfilled. Data files, benchmark values,
pipeline constants and prose get caught; **hard-coded expected numbers inside tests are the
blind spot**.

- Backfill the expectation — or better, restate the assertion **convention-independently**
  (record the value; assert a qualitative fact), so the next convention change does not break
  the test for the wrong reason.
- A test failing only because a convention moved is **indistinguishable** from one that
  caught a real regression. That ambiguity is the cost of encoding raw thresholds.

---

# Reproducibility

- Fix random seeds; record the seed with the result.
- Record dependency versions (lockfile or environment file).
- Store the exact configuration that produced each artifact; do not rely on shell history.
- Generated artifacts are not sources of truth: keep the recipe (script + config), not only the output.

---

# Forbidden Practices

| Forbidden | Reason | Detection |
|-----------|--------|-----------|
| Skipping the validation gate before downstream use | Non-physical/non-conforming output silently propagates | Static import+call check |
| Mixing unit systems without explicit conversion | Order-of-magnitude errors | Grep for bare numeric factors plus unit annotations |
| Hard-coded physical constants | Drift between modules | Import from one constants module |
| Returning raw arrays with implicit column meaning | Downstream cannot verify names/semantics | Require a named structure (DataFrame / dataclass) |
| Relying on a test that only encodes a raw threshold | Convention changes break it for the wrong reason | Prefer qualitative or reference-derived assertions |
| Committing credentials, absolute paths, or local data | Leakage and non-reproducibility | Release hygiene gate |
