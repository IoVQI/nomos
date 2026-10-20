---
project_version: "0.9.0"
document_version: "1.0"
language: "en"
last_updated: "2026-08-17"
category: "ai_rules"
tags: [debug, numerical, model, solver]
---

# Numerical Debug Checklist

---

# Always Check

1. Units
2. Boundary conditions
3. Sign conventions
4. Interpolation behavior
5. Numerical convergence
6. Conservation laws

---

# model Debugging

Check:
- monotonicity
- causality
- smooth derivatives
- interpolation oscillation

Possible issues:
- spline overshoot
- negative pressure
- discontinuous sound speed

---

# solver Debugging

Common failures:

1. Divergence near center
2. Negative mass
3. Pressure increasing outward
4. Surface never reached

Always inspect:
- dr step size
- center expansion
- stopping condition

---

# Plasma Simulation Debugging ⚠️ 已废弃 (2026-07-21)

> 与当前研究方向无关。保留作为历史参考。

Always verify:
- CFL condition
- timestep stability
- numerical dispersion
- energy conservation

Check for:
- grid heating
- aliasing
- boundary reflection

---

# AI Debug Behavior

When debugging:
1. identify root cause
2. explain physical meaning
3. explain numerical meaning
4. propose minimal fix
5. provide corrected code

Never:
- patch symptoms blindly
- suppress warnings without explanation