# Uniqueness of Recursive Utility with Unbounded Consumption and Non-Expected Utility

**Authors:** Luigi Montrucchio, Lorenzo Stanca
**arXiv:** 2610.03157 ([abs page](https://arxiv.org/abs/2610.03157)) | **Primary category:** econ.TH | **Also in:** -
**v1 submitted:** 2026-10-02

## TL;DR
The paper derives order-theoretic fixed-point conditions for the existence, non-existence, uniqueness, and global attractivity of stochastic recursive utility when per-period consumption is unbounded and preferences may be non-expected-utility (Epstein–Zin, smooth ambiguity, multiple priors, Hansen–Sargent robustness). All conditions collapse to transparent bounds on an "adjusted consumption growth" ratio `M(C)/C` against discount-factor thresholds `β^{1/|r|}` and `β^{-1/r}`, which the authors verify in canonical macro-finance calibrations — closing, among other things, the previously open uniqueness question for smooth-ambiguity utility under the Ju–Miao calibration. A key conceptual message is that uniqueness is inherently class-relative: with non-unit EIS it holds within the "separable" class `U_t = φ(z_t)C_t`, while at unit EIS genuine multiplicity can arise (two distinct utilities in the constant-volatility Bansal–Yaron model).

## Research Question
Given a (possibly unbounded) consumption process `C` and a recursive preference built from a time aggregator `W` and a certainty equivalent `M`:
1. When does the forward-looking fixed-point equation `U = W(C, M(U))` have a solution — and when can non-existence be *proved*?
2. When is that solution unique, and unique *in which class* of utility processes?
3. Do iterates of the recursion converge to the solution from arbitrary starting points (global attractivity), which matters for computation?

The motivation is that contraction-metric methods (Marinacci–Montrucchio 2010) require bounded consumption, while spectral and Orlicz-space methods are largely tied to Epstein–Zin; applied work with ambiguity or Gaussian/Poisson growth shocks has lacked general answers.

## Model and Setup
- **Environment:** a filtered probability space with discrete time; strictly positive adapted consumption `C ∈ L++`. The working space is the weighted `L¹` space `L¹(δ)` with norm `Σ_t δᵗ E|X_t|` — an `L¹` analogue of Boyd's weighted supnorm. It is a Dedekind σ-complete Banach lattice; notably its positive cone has empty interior, which blocks the Du-type fixed-point theorem used by Ren–Stachurski.
- **Preferences:** CES aggregator `W(x,y) = ((1−β)xʳ + βyʳ)^{1/r}` with `r < 0` (EIS < 1) or `0 < r < 1` (EIS > 1), plus the Cobb–Douglas limit `x^α y^β` (EIS = 1, focus on `α+β=1`). The certainty equivalent `M` is assumptions-light: monotone, σ-order continuous, subhomogeneous (linked to increasing relative risk aversion); **order concavity** (a risk/ambiguity-aversion property) is the key added assumption for uniqueness. Attention is restricted to one-step certainty equivalents, `M_t(U) = M_t(U_{t+1})`.
- **Solution concept:** fixed points of `TX = W(C, M(X))` lying in the cone `K(C) = ⋃_{0<λ<μ} [λC, μC]` of processes *comparable to consumption* — i.e., utilities with wealth-consumption ratio `U/C` bounded above and below. Uniqueness claims are relative to this cone (or, in the Markov case, to the separable class).
- **Markov specialization:** state `ξ = (z,y)` with transition `Q(z,·)×ν` and log growth `g_{t+1} = κ(z_t, z_{t+1}, y_{t+1})`. When `M` is *conditionally positively homogeneous* and *stationary*, `M(C_{t+1}) = C_t h(ξ_t)`, and the problem reduces to **separable** utilities `U_t = φ(z_t)C_t`, where `φ` is a fixed point of the operator `Aφ = Γ_r(Hφ)`, `Hφ = M(e^κ φ)`, `Γ_r(t) = ((1−β)+βtʳ)^{1/r}`, with `H1 = h`. The hidden-regime model of Ju–Miao is recast in this form with the belief `µ_t ∈ [λ₂₁, λ₁₁]` as the state.

## Main Results
- **Existence (Props. 3, 5):** For low EIS (`r<0`), existence in `K(C)` requires `M(C)/C ≫ β^{1/|r|}` — the adjusted growth measure `(1/β)(M(C)/C)^{|r|}` uniformly bounded away from zero: *consumption cannot grow too slowly*. For high EIS (`0<r<1`), `M(C)/C ≪ β^{-1/r}`: *consumption cannot grow too fast*. Proofs are monotone iterations from the endpoints of an invariant order interval, yielding least and greatest fixed points.
- **Uniqueness (Props. 4, 6):** With `M` order concave, no fixed point lies on the *lower perimeter* of the invariant interval, and a theorem of Marinacci–Montrucchio (2019) delivers a unique fixed point in `K(C)`. For `r<0` nothing beyond the existence condition is needed; for `0<r<1` one adds `0 ≪ M(C)/C`.
- **Unit EIS (Props. 8–9, Remark 10):** `T` is β-subhomogeneous, and existence *and* uniqueness in `K(C)` hold iff `M(C) ∈ K(Cᵖ)`, `p = (1−α)/β` (so `M(C) ∈ K(C)` when `α+β=1`). Remark 10 is important: with positively homogeneous `M`, every fixed point generates a continuum of non-comparable fixed points `V(λ)_t = λ^{β^{−t}}U_t` — uniqueness genuinely fails in the full space, and a deterministic example (`C ≡ 1`) exhibits spurious fixed points outside `K(C)` for CES as well.
- **Cone generalization (Prop. 11):** each admissible cone `K(Z)` with `M(Z) ∈ K(C^{−α/β}Z^{1/β})` contains exactly one fixed point; for Epstein–Zin, admissible `Z` solve `E_t[Z_{t+1}^s] = C_t^{−αs/β}Z_t^{s/β}B_t`.
- **Global attractivity (Prop. 12):** uniqueness implies `Tⁿ(X) → U` in order and in `L¹(δ)`-norm from *any* `X ∈ K(C)` — value-function iteration converges.
- **Non-existence (Props. 13–14):** with `M` positively homogeneous, `M(C)/C ≥ β^{−1/r}` everywhere (for `0<r<1`) kills all fixed points in `L⁺` (mirror image for `r<0`); weaker conditions (`sup M(C)/C = ∞`, resp. `inf = 0`) kill all fixed points in `K(C)`. The sufficient conditions are therefore "almost" necessary.
- **Markov/separable results (Props. 15–16):** with `h = M(e^κ)`, high-EIS existence needs `sup h < β^{−1/r}`, low-EIS needs `inf h > β^{1/|r|}`; under order concavity `A` has a unique fixed point, yielding `U_t = φ(z_t)C_t`. Crucially, uniqueness of `A`'s fixed point does **not** require `inf h > 0`, so a unique *separable* utility can exist even when uniqueness of `T` in `K(C)` fails — separability acts as a selection device.
- **Applications:**
  - *Mehra–Prescott/Weil* (`β=0.95`, `ℓ=(1.054, 0.984)`): `1.008 ≤ h(i) ≤ 1.024` clears both thresholds (`β^{1/9} ≈ 0.9943`, `β^{−1} ≈ 1.053`), so existence and uniqueness hold throughout; but a 5% growth increase (high EIS, `s=−9`) or a 3% reduction (low EIS) suffices for non-existence — for EIS > 9.6 or EIS < 0.2 respectively.
  - *Ju–Miao hidden regime:* closed-form `h(µ) = {µe^{ηa₁} + (1−µ)e^{ηa₂}}^{1/η}`; under their calibration `max h ≈ 1.019 < β^{−1/r} ≈ 1.079`, establishing the previously unresolved **uniqueness of smooth-ambiguity utility** (`r=1/3, s=−1, η=−7.864`), plus robust control at unit EIS (`h ∈ [0.968, 1.019]`) and multiple priors (`h_MP ≈ 0.9339`). Counterfactual non-existence requires ≈8.3% higher gross growth (smooth ambiguity) but ≈15.5% (multiple priors).
  - *Rare disasters (Bidder–Smith, EIS = 1.9):* `h(H) = B_s e^{A_s H}` with `B_s ≈ 1.00146 < β^{−1/r} ≈ 1.00169`, so existence holds, but `inf h = 0` violates the uniqueness condition for `T`; nevertheless a unique **separable** utility exists. At unit EIS, two separable utilities live in disjoint cones, `U^{(i)} ≈ C_t e^{c_i + b_iH_t}` (coefficients −83.39, −278.1), matching Christensen's affine solutions.
  - *Bansal–Yaron Case I at unit EIS:* two separable utilities — log-linear `U^{(0)} ≈ C_t e^{0.1121+43.47X_t}` and a new log-quadratic `U^{(1)} ≈ C_t e^{−1.219−46.53X_t−2.051×10⁴X_t²}` — with `U^{(1)} < U^{(0)}` everywhere.

## Methodology
Pure order-theoretic fixed-point theory in Banach lattices: Kantorovich's theorem (monotone iteration on invariant order intervals, exploiting Dedekind σ-completeness / monotone convergence in `L¹(δ)`), Krasnosel'skii's theory of positive operators, and — as the uniqueness workhorse — Marinacci–Montrucchio's "unique Tarski fixed points" theorem, applied by showing no fixed point sits on the lower perimeter of the order interval. This avoids the alternative route of computing spectral radii of supergradients (Amann). A remark shows the Thompson metric turns `A` into a `p`-contraction. The applications combine closed-form computation of `h` using Gaussian/Poisson/ARG moment formulas with an exponential ansatz `Z_t = C_t e^{(qX_t²+bX_t)/s}` to construct admissible cones at unit EIS.

## Relation to Literature
- **vs. Marinacci–Montrucchio (2010):** contraction metrics require bounded `C`; this paper handles unbounded `C` via order theory.
- **vs. Borovička–Stachurski (2020, JF):** they obtain *necessary and sufficient* conditions for Epstein–Zin with compact state spaces; this paper trades necessity for breadth (non-EU certainty equivalents, some unbounded states).
- **vs. Hansen–Scheinkman (2009, 2012):** their spectral approach is Epstein–Zin-specific; the present framework accommodates a broader class of certainty equivalents.
- **vs. Christensen (2022, JET):** exponential-Orlicz spaces with thin-tail conditions, largely unit EIS; here broader preferences plus global attractivity; the unit-EIS disaster-model solutions coincide with his Proposition 2.2.
- **vs. Pohl–Schmedders–Wilms (2024, RFS):** their Jensen/Minkowski-based existence bounds are logically non-comparable with the conditions here (neither implies the other).
- **vs. Ren–Stachurski / Du:** Du's fixed-point theorem needs a cone with nonempty interior; `L¹`'s positive cone has empty interior, motivating the different toolkit.
- Also positioned relative to the dynamic-programming strand (Le Van–Vailakis, Martins-da-Rocha–Vailakis, Bloise–Vailakis, Balbus, Bloise–Le Van–Vailakis) and forward-looking equilibrium equations (Beker–Chen).

## Comments
- **Strengths:**
  - Proving uniqueness for smooth-ambiguity utility under the Ju–Miao calibration closes a genuine open problem; more broadly, this is the first framework to deliver existence + uniqueness + global attractivity for non-EU certainty equivalents with unbounded consumption.
  - The conditions are unusually usable: everything reduces to comparing `h` against `β^{1/|r|}` or `β^{−1/r}`, with clean economics ("consumption cannot grow too slowly/too fast").
  - The lower-perimeter uniqueness argument is elegant and simpler than the spectral-radius route; the observation that `A`'s fixed point is unique *without* `inf h > 0` — making separability a selection device when full uniqueness fails — is a genuinely novel conceptual contribution.
  - The fragility quantifications (5%/3% in Weil's calibration; 8.3%/15.5% in Ju–Miao's) are striking, practitioner-relevant warnings.
  - The paper is honest about what it does not claim (e.g., non-separable utilities are not ruled out in the disaster model).
- **Weaknesses / concerns:**
  - "Uniqueness" is always class-relative — within `K(C)` (bounded wealth-consumption ratio) in general, within the separable class in Markov settings. Remark 10 exhibits a *continuum* of non-comparable fixed points at unit EIS, and the deterministic example shows spurious fixed points outside `K(C)` even with CES. Whether out-of-cone fixed points are economically irrelevant is asserted (they blow up or vanish) rather than analyzed.
  - Conditions are sufficient, not necessary, outside the positively homogeneous case, and the gap is economically real: in the paper's own rare-disaster model with EIS < 1, `inf h = 0` triggers Prop. 14's non-existence in `K(C)` — a substantive case (low-EIS disaster economies exist in the literature) that the paper never discusses, even though it flags the mirror-image claim for Bansal–Yaron with EIS > 1 in a single sentence.
  - The order-concavity workhorse requires `s ≤ 1` (RRA ≥ 0) and, for smooth ambiguity, `η ≤ 1`; risk-seeking or ambiguity-seeking specifications are uncovered (an EZ-specific dual argument in §3.6 partially fills `s > r > 0`).
  - There is a mismatch between the abstract generality (any monotone subhomogeneous `M`) and the Markov machinery (conditional positive homogeneity + stationarity), which excludes exactly the non-homogeneous quasi-arithmetic CEs the abstract part accommodates.
  - The Hansen–Sargent application is confined to unit EIS; non-unit-EIS robust control is not treated.
  - The introduction motivates uniqueness via indeterminate asset-pricing and welfare implications, but no pricing implications of the documented multiplicity are computed.
- **Suggestions:**
  - Quantify the multiplicity: compute price-dividend ratios or risk-free rates under the two unit-EIS utilities in Bansal–Yaron Case I to show whether multiplicity matters for *prices*, not just utility levels.
  - Ask which fixed point finite-horizon backward induction (a terminal condition) selects — the natural transversality-type selection; Prop. 12 answers this only within `K(C)`.
  - Try to construct, or rule out, non-separable fixed points in the rare-disaster model with non-unit EIS.
  - Spell out the EIS < 1 disaster case and elaborate the one-sentence EIS > 1 non-existence claim for long-run risk, connecting it to Pohl–Schmedders–Wilms's wealth-consumption-ratio results.
  - Make the Thompson-metric `p`-contraction of `A` into an explicit algorithmic statement with convergence rates.
  - Clarify whether "utility comparable to consumption" (`K(C)`) is a behavioral/transversality admissibility axiom or a technical convenience.

## Tags
#recursive-utility #macro-finance #fixed-points #order-theory #epstein-zin #ambiguity #unbounded-consumption #asset-pricing
