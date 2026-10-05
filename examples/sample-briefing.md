# arXiv econ.TH daily briefing - 2026-10-05



Papers announced today (new + cross-lists): **2**. Reports generated: **2**.



## Overview



**Signaling via Money** - Olivier Bos, Martin Pollrich ([arXiv:2610.03146](https://arxiv.org/abs/2610.03146))

> The paper studies mechanism design with aftermarkets whose beliefs about agents' types enter agents' payoffs, and asks whether making monetary transfers publicly observable constrains what a designer can implement. The main result (Theorem 1) shows that any outcome implementable with hidden transfers (plus designer-chosen signals) can be approximated arbitrarily well by a mechanism with fully public transfers. Observability of money thus costs at most a vanishing distortion, which rationalizes the standard — and previously unexamined — modeling assumption that transfers stay hidden from aftermarkets.

**Uniqueness of Recursive Utility with Unbounded Consumption and Non-Expected Utility** - Luigi Montrucchio, Lorenzo Stanca ([arXiv:2610.03157](https://arxiv.org/abs/2610.03157))

> The paper provides order-theoretic fixed-point conditions for the existence, non-existence, uniqueness, and global attractivity of stochastic recursive utility when consumption is unbounded and preferences need not be expected utility (Epstein–Zin, smooth ambiguity, multiple priors, Hansen–Sargent robust control). The novelty is a comparatively simple uniqueness argument — inspecting the behavior of the concave recursive operator on the "lower perimeter" of its domain (Marinacci–Montrucchio's unique-Tarski theorem) — which in a Markov setting yields uniqueness within a *separable* class U = φ(z)·C for non-unit EIS, and closes a open gap by proving uniqueness of smooth-ambiguity utility under the Ju–Miao calibration. Applied payoffs include simple, interpretable parameter tests (a threshold on an "adjusted consumption growth" ratio M(C)/C) and new multiplicity results at unit EIS in rare-disaster and Bansal–Yaron environments.


---


# Full reports

# Signaling via Money

**Authors:** Olivier Bos, Martin Pollrich
**arXiv:** 2610.03146 ([abs page](https://arxiv.org/abs/2610.03146)) | **Primary category:** econ.TH | **Also in:** -
**v1 submitted:** 2026-10-02

## TL;DR
The paper studies mechanism design with aftermarkets whose beliefs about agents' types enter agents' payoffs, and asks whether making monetary transfers publicly observable constrains what a designer can implement. The main result (Theorem 1) shows that any outcome implementable with hidden transfers (plus designer-chosen signals) can be approximated arbitrarily well by a mechanism with fully public transfers. Observability of money thus costs at most a vanishing distortion, which rationalizes the standard — and previously unexamined — modeling assumption that transfers stay hidden from aftermarkets.

## Research Question
- Does public observability of transfers restrict the set of implementable social choice functions (SCFs) in environments where post-mechanism beliefs about agents' private information are payoff-relevant?
- Formally, how does the implementable set under *signaling mechanisms* Γ^s (transfers hidden, aftermarket observes allocation k and signal s) compare with the set under *public transfers mechanisms* Γ^p (no signals, the entire outcome (k, t) is public)?
- Can observable transfers themselves replicate the informational role of explicit signals?

## Model and Setup
- **Environment.** A designer with no value allocates a single object among n ≥ 1 agents with independent private valuations v_i drawn on compact supports V_i = [v̲_i, v̄_i] ⊂ ℝ₊; feasible allocations K = {0, 1, …, n} (0 = seller keeps the object). An SCF is (k, t) with k: ΠV_i → K and t_i: ΠV_i → ℝ; implementation is in the interim (Bayes–Nash) sense — allocations and *expected* transfers must coincide.
- **Aftermarket / belief-dependent payoffs.** After the mechanism, a Bayesian game unfolds with a third party (or general public) whose posterior beliefs are a joint distribution F ∈ Δ(V₁ × ⋯ × V_n). Agent i's utility is
  v_i·1{k=i} − t_i + Φ_i(v_i, k, F),
  where Φ_i is assumed monotone and continuous. This is a *reduced form*: continuation payoffs may stem from strategic outsider responses, provided they depend on observables only through the induced posteriors.
- **Mechanisms.** Both classes randomize via a public draw U[0,1]:
  - Signaling mechanism Γ^s: σ: M₁ × ⋯ × M_n × [0,1] → K × ℝⁿ × S. The public observes (k, s) but neither transfers nor messages.
  - Public transfers mechanism Γ^p: σ: M₁ × ⋯ × M_n × [0,1] → K × ℝⁿ. The entire (k, t) is publicly observable; messages remain private.
- **Solution concept.** Bayes–Nash equilibrium, with ε-Bayes–Nash equilibrium for the approximation result.

## Main Results
**Theorem 1 (Approximate Implementability Equivalence):**
- **(i)** Any SCF implementable by a signaling mechanism is *approximately* implementable by a public transfers mechanism: for every ε > 0 there exists a public transfers mechanism with an ε-BNE whose induced allocation probabilities and interim expected transfers *exactly* match (k, t), and whose interim expected payoffs are within ε.
- **(ii)** Any SCF implementable by a public transfers mechanism is implementable by a signaling mechanism (let the signal simply be the realized transfer vector, so the aftermarket is informationally unaffected).

**Proof of (i) — the ε-mixing construction.** The public mechanism is direct and mimics Γ^s's equilibrium behavior for each reported profile. With probability 1 − δ it pays b̃_i(k, s) = f_i(k, s), where f: K × S → ℝⁿ is *injective*, so observing (k, b̃) induces exactly the same posteriors as (k, s). With probability δ it pays an adjustment transfer T̂_i(v′) (depending only on the report v′) that restores the interim expected transfer T_i(v′) exactly; T̂_i generically scales like 1/δ. Since Φ_i is continuous on a compact domain (V_i compact, K finite, Δ(V₁ × ⋯ × V_n) compact in the weak topology), |Φ_i| ≤ C < ∞, so the payoff distortion on the rare event is at most 2Cδ and truthful reporting is a 4Cδ-BNE; choosing 4Cδ < ε completes the proof. The rare-event/large-transfer device is explicitly likened by the authors to Crémer–McLean (1988). Footnote 3 concedes that under limited liability one must fix δ away from zero, obtaining only close (not converging) approximation.

**Example 1 (Bos–Pollrich 2025 environment).** With linear reputational payoffs Φ_i = λE[V_i | F] (λ > 0) and auctions where k = i iff t_i = max_j t_j, the approximate equivalence of Theorem 1 strengthens to an *exact* equivalence.

**Remark 1 (Rivera Mora 2024).** The result is an approximate counterpart to his revelation principle for belief-dependent preferences, within the subclass where payoffs depend on observables only through first-order posteriors — preserving the shortcut of identifying a type with its expected transfer.

**Dworczak (2020) connection.** The information partition induced by cutoff mechanisms and post-allocation signals can be approximated arbitrarily closely by publicly observed transfers, via the same ε-mixing device.

**Example 2 (illustration).** Two agents with binary valuations {L, H} and utility αE[V_i | O], α ≥ 0; efficient allocation with winner payments τ_L < τ_H. The signaling mechanism uses s ∈ {0,1} (s = 1 iff the winner pays τ_H). The public transfers mechanism encodes the signal into money via the injective map f(k, s) = 10·1{k=1} + 20·1{k=2} + s, then applies the ε-mixing device. The example is deliberately incomplete — the authors note (fn. 4) that computing IC/IR would require specifying the type distribution.

## Methodology
Classical Bayesian mechanism design, executed constructively:
- Revelation-principle–style direct-mechanism transformations of an arbitrary equilibrium of Γ^s.
- Approximate implementation via ε-BNE and vanishing-probability mixing.
- A Crémer–McLean-flavored rare-event/large-magnitude transfer device that *separates the informational role of transfers (injective encoding f) from their incentive role (adjustment T̂_i(v′))*.
- Analytical compactness/continuity arguments yielding the uniform bound C on continuation payoffs — the proof deliberately does not track the posteriors induced on the δ-event.
- Illustrative examples calibrating the general theorem to specific applied environments (reputational auctions, cutoff structures). No dynamic programming, lattice theory, or axiomatics; the technical demands are modest, with the contribution sitting in the question and the construction.

## Relation to Literature
- **Mechanisms with aftermarkets:** Dworczak (2020) characterizes implementability via cutoff mechanisms; this paper shows his induced information structure (cutoffs + signals) can be mimicked by observable transfers, broadening implementability analysis beyond the cutoff class.
- **Signaling auctions:** Bos–Pollrich (2025) show how disclosure shapes revenue with reputational bidders; the present result complements this by showing transfer observability costs at most a vanishing implementability distortion.
- **Belief-dependent preferences:** Rivera Mora (2024) provides a revelation principle allowing observable, hidden, or partially observable transfers — but takes the observability regime as given; this paper studies what that regime costs, obtaining an approximate counterpart in first-order-belief environments.
- **Privacy and disclosure:** Calzolari–Pavan (2006a,b) ask when *not* disclosing is optimal; Eilat–Eliaz–Mu (2025) treat payment observability as a design constraint in privacy-preserving auctions; Haupt–Hitzig (2026) constrain designer learning. This paper departs by asking a structural implementability question rather than an optimal-design one.
- **Credibility/transparency:** Akbarpour–Li (2020), Hakimov–Raghavan (2026), Möller (2026) on how transparency shapes implementable outcomes; classical roots in Gibbard (1973) and Myerson (1981).

## Comments
- **Strengths:**
  - A clean structural question with a clean answer: whether observability of money *per se* constrains implementability had not been isolated, and the answer is "essentially no" — a useful foundational fact for the growing aftermarket/privacy literature.
  - The injective encoding b̃_i = f_i(k, s) makes "money as a signal" literal and transparent, and the separation of transfers' informational and incentive roles is genuinely elegant.
  - Assumptions on primitives are weak: no distributional details are needed (the proof works for any product of compactly supported independent types), Φ_i is general within the belief-based class, and the reduced form covers strategic outsider responses.
  - It unifies and calibrates several strands: an exact equivalence for the Bos–Pollrich environment (Example 1), an approximate counterpart to Rivera Mora (Remark 1), and an approximation of Dworczak's cutoff-based information structure.
- **Weaknesses / concerns:**
  - **Unbounded transfers are doing the work.** T̂_i(v′) scales like 1/δ, and the encoding payments (e.g., 10, 20, 21 in Example 2) are arbitrary code values. Under limited liability, budget balance, risk aversion, or the non-negative payments standard in auctions, the construction fails — acknowledged in footnote 3 and the conclusion, but this sharply limits the practical reading of "vanishing distortion."
  - **Approximation, not equivalence.** The result is ε-BNE (not exact) and interim (not dominant-strategy) implementation; moreover, only *interim expected* transfers are matched — realized ex-post transfer profiles can differ wildly from the original SCF's, which matters for any ex-post concern.
  - **Reduced-form restriction on continuation payoffs.** Φ_i must depend on observables only through posterior beliefs, excluding higher-order beliefs (Rivera Mora's more general class) and signal-dependent aftermarket protocols (e.g., resale bargaining that responds to more than posteriors).
  - **Limited novelty of technique.** Once transfers are allowed to be arbitrary observables, injective encoding of signals is near-mechanical, and the adjustment-on-a-vanishing-event step is Crémer–McLean-flavored; the contribution is the formulation and clean statement rather than deep method.
  - **Example 2 is a sketch**: no type distribution is specified, IC/IR for (τ_L, τ_H) are asserted rather than verified, and the equilibrium is not computed. The monotonicity assumption on Φ_i also does not appear to be used in the proof of Theorem 1 (only continuity and compactness are invoked).
  - **Scope:** single object, independent private values, one-dimensional types; and the theorem speaks only to the implementable *set*, not to optimal design under realistic constraints — where observability may still matter (cf. Eilat et al.).
- **Suggestions:**
  - Prove an impossibility or lower-bound result: is *exact* implementation with public transfers impossible in some environment, so the approximation is tight? How fast must transfer magnitudes grow as ε → 0?
  - Characterize environments where *bounded* transfers suffice (the authors' own open question) — e.g., finite type spaces, restricted signal structures, or when the encoding can be shifted into the allocation's randomization.
  - Complete Example 2: specify p = Pr(V_i = H), solve IC/IR explicitly, and compute the realized distortion bound as a function of δ and α.
  - Address risk aversion: with concave utility in money, the 1/δ construction is costly — does the equivalence survive?
  - Clarify the role (if any) of the monotonicity of Φ_i, and discuss measure-theoretic conditions on S for the injective encoding (|S| ≤ continuum).
  - Examine robustness to unbounded Φ_i or to off-path beliefs on the δ-event, where full revelation of reports plausibly occurs.
  - Consider a designer constrained to "natural" (e.g., monotone, non-negative) payment rules — does observability then bind? This would connect the theorem to the privacy literature more substantively.

## Possible Publication Venues
1. **Journal of Economic Theory** — *strong fit*: an implementability/revelation-principle contribution in the lineage of Rivera Mora (2024) and Calzolari–Pavan (2006b); the right scope and technical register for a single-theorem result.
2. **Economic Theory** — *strong fit*: a compact mechanism-design note with a clean equivalence result fits the journal's format and audience well.
3. **Games and Economic Behavior** — *plausible*: the natural continuation of Bos–Pollrich (2025, GEB) on signaling auctions; the aftermarket/auction audience is there, though the paper is more implementation-theoretic than game-theoretic.
4. **Theoretical Economics** — *plausible*: adjacent to the Dworczak aftermarkets community, but the paper's brevity and narrow scope may fall short of the journal's bar without substantive extensions (bounded transfers, optimal design implications).

## Tags
#mechanism-design #signaling #aftermarkets #information-disclosure #implementation-theory #auctions #privacy

# Uniqueness of Recursive Utility with Unbounded Consumption and Non-Expected Utility

**Authors:** Luigi Montrucchio, Lorenzo Stanca
**arXiv:** 2610.03157 ([abs page](https://arxiv.org/abs/2610.03157)) | **Primary category:** econ.TH | **Also in:** -
**v1 submitted:** 2026-10-02

## TL;DR
The paper provides order-theoretic fixed-point conditions for the existence, non-existence, uniqueness, and global attractivity of stochastic recursive utility when consumption is unbounded and preferences need not be expected utility (Epstein–Zin, smooth ambiguity, multiple priors, Hansen–Sargent robust control). The novelty is a comparatively simple uniqueness argument — inspecting the behavior of the concave recursive operator on the "lower perimeter" of its domain (Marinacci–Montrucchio's unique-Tarski theorem) — which in a Markov setting yields uniqueness within a *separable* class U = φ(z)·C for non-unit EIS, and closes a open gap by proving uniqueness of smooth-ambiguity utility under the Ju–Miao calibration. Applied payoffs include simple, interpretable parameter tests (a threshold on an "adjusted consumption growth" ratio M(C)/C) and new multiplicity results at unit EIS in rare-disaster and Bansal–Yaron environments.

## Research Question
When does the recursion U_t = W(C_t, M_t(U_{t+1})) — with a CES or Cobb–Douglas time aggregator W and a possibly non-expected-utility certainty equivalent M — admit a solution, when is that solution unique, when does it fail to exist, and do iterates of the operator converge to it, in environments where per-period consumption is unbounded (e.g., Gaussian or Poisson-disaster growth)? The companion question: within the natural Markov class, can the infinite-dimensional fixed-point problem for a utility *process* be reduced to a fixed-point problem for a single *function* of the state, and is that reduced solution unique?

## Model and Setup
- **Environment:** Discrete time on (Ω, Σ, P) with filtration (Σ_t). Consumption C ∈ L^1_{++}(δ), the weighted L¹ space on Ω×T with measure P⊗c_δ (δ^t point masses) — an L¹ analogue of Boyd's weighted sup-norm — which is a Dedekind σ-complete Banach lattice (so monotone iterates have suprema/infima in the space).
- **Aggregators:** CES W(x,y) = ((1−β)x^r + βy^r)^{1/r} with EIS = 1/(1−r), splitting into r < 0 (EIS < 1), 0 < r < 1 (EIS > 1), and the r → 0 Cobb–Douglas limit x^{1−β}y^β (unit EIS).
- **Certainty equivalent M:** deliberately minimal assumptions — (i) monotone, (ii) σ-order continuous, (iii) subhomogeneous (linked to increasing relative risk aversion), plus **order concavity** for uniqueness. This covers quasi-arithmetic means with IRRA (Kreps–Porteus/EZ: M_t(X) = (E_t X^s_{t+1})^{1/s}, RRA = 1−s), smooth ambiguity (second-stage power η), multiple priors (η → −∞), and robust control.
- **Solution concept:** recursive utility is a fixed point of T X = W(C, M(X)) lying in the cone **K(C)** = ⋃_{0<λ<μ} [λC, μC] of processes comparable to C (comparable long-run growth rates), for some δ > 0.
- **Markov specialization:** state ξ_t = (z_t, y_t) with transition Q×ν and consumption growth g_{t+1} = κ(z_t, z_{t+1}, y_{t+1}); under conditional positive homogeneity and stationarity of M, one searches among **separable** utilities U(ξ) = φ(ξ)C(ξ), with φ a fixed point of (Aφ)(z) = Γ_r(Hφ(z)), Γ_r(t) = ((1−β)+βt^r)^{1/r}, and h(z) := (H1)(z) = M_z(e^{κ(z,·)}) the certainty-equivalent growth factor.

## Main Results
Abstract layer (Section 3):
1. **Existence, low EIS (Prop. 3):** if M(C)/C ≫ β^{1/|r|}, T maps K(C) into itself and has a greatest fixed point. The ratio (1/β)(M(C)/C)^{|r|} ≫ 1 is an *adjusted consumption growth* measure — consumption cannot grow too slowly.
2. **Uniqueness, low EIS (Prop. 4):** under the same conditions plus **order concavity** of M, the fixed point in K(C) is unique — no extra growth restriction needed. Economically: risk/ambiguity aversion rules out multiple continuation values.
3. **Existence/uniqueness, high EIS (Props. 5–6):** mirror-image conditions 0 ≪ M(C)/C ≪ β^{−1/r} (consumption cannot grow too fast; the lower bound is the lower-perimeter condition).
4. **Unit EIS (Props. 8–9, 11):** the Cobb–Douglas operator is β-subhomogeneous; existence *and* uniqueness in K(C) hold iff M(C) ∈ K(C) — with a remarkable twist: at unit EIS with homogeneous M, every fixed point generates a continuum of non-comparable fixed points (Remark 10), so uniqueness is intrinsically cone-relative. Prop. 11 characterizes admissible cones K(Z) and, for Epstein–Zin, all generators Z via condition (15), with closed-form utility U = B^{β/(sα)}Z.
5. **Global attractivity (Prop. 12):** uniqueness implies T^n(X) → U in order and L¹(δ)-norm from any X ∈ K(C) — a computational guarantee.
6. **Non-existence (Props. 13–14):** under positive homogeneity, M(C)/C ≥ β^{−1/r} (high EIS) or ≤ β^{1/|r|} (low EIS) rules out any fixed point; weaker conditions (sup M(C)/C = ∞, or inf = 0) rule out fixed points in K(C). The sufficient conditions are thus "almost" necessary.

Markov layer (Section 4): conditions become tests on h — e.g., for 0 < r < 1: sup_z h(z) < β^{−1/r} and inf_z h(z) > 0. With non-unit EIS, whenever a separable utility exists it is **unique within the separable class** (Prop. 15), even when full uniqueness fails. Applications:
- **Mehra–Prescott/Weil:** under Weil's calibration (ℓ₁ = 1.054, ℓ₂ = 0.984, β = 0.95) one has 1.008 ≤ h(i) ≤ 1.024, safely between the thresholds, so existence and uniqueness hold throughout r, s ∈ [−9,0)∪(0,1); a ~5% growth increase (high EIS) or ~3% reduction (low EIS) triggers non-existence.
- **Ju–Miao hidden-regime model:** existence and uniqueness verified for smooth ambiguity (r = 1/3, η = −7.864), Hansen–Sargent robust control (unit EIS), and multiple priors — notably **closing the open uniqueness question for smooth ambiguity**; non-existence counterfactuals require ~8.3% (smooth ambiguity) vs ~15.5% (multiple priors) gross-growth increases, the latter independent of regime persistence.
- **Bidder–Smith rare disasters with EIS = 1.9:** existence holds (h(0) = B_s ≈ 1.00146 < β^{−19/9} ≈ 1.00169) but the uniqueness condition fails (inf h = 0 as disaster intensity H → ∞); a **unique separable** utility survives. At unit EIS, two separable utilities coexist in disjoint cones, matching Christensen's affine solutions.
- **Bansal–Yaron (constant volatility, unit EIS):** two distinct separable utilities, U⁽⁰⁾ log-linear and U⁽¹⁾ log-quadratic in the state, with U⁽¹⁾ < U⁽⁰⁾ everywhere — the log-quadratic solution is new.

## Methodology
Pure order-theoretic fixed-point theory in Banach lattices, combined with sharp probabilistic computation:
- **Kantorovich/Krasnosel'skii monotone iteration** on order intervals [εC, (1−β)^{1/r}C] to get extremal fixed points (existence).
- **Lower-perimeter uniqueness** (Marinacci–Montrucchio 2019, *Math. OR*, Theorem 1 and its dual): show no fixed point sits on ∂⋄ of the invariant interval; this replaces spectral-radius-of-subgradient computations (Amann, Christensen). A Thompson-metric p-contraction route (via k-subconcavity of A) is also sketched.
- **Subhomogeneous / q-subhomogeneous operator theory** for the Cobb–Douglas case, where β-subhomogeneity makes existence and uniqueness coincide.
- **Cone arithmetic** (K(X) comparable-process cones) as the organizing domain concept; change of variables to u = U/C and the wealth–consumption ratio ψ = u^r to connect to the EZ literature.
- **Markov reduction** to separable utilities via conditional positive homogeneity and stationarity; then closed-form computation of h for regime-switching, Gaussian learning (Bayes recasting of the hidden regime as a Markov belief process on K = [λ₂₁, λ₁₁]), Poisson disasters with ARG intensity, and Gaussian AR(1) long-run risk.

## Relation to Literature
- **Marinacci–Montrucchio (2010, JET):** the contraction-metric strand this paper supersedes; contraction required bounded consumption, violated by Gaussian errors.
- **Borovička–Stachurski (2020, JF):** obtain *necessary and sufficient* conditions for Epstein–Zin but with compact state space; this paper trades sharpness for breadth (non-EU certainty equivalents, sometimes unbounded state).
- **Hansen–Scheinkman (2009, 2012):** spectral approach, EZ only; the present conditions accommodate broader certainty equivalents.
- **Christensen (2022, JET):** exponential-Orlicz spaces, noncompact/unbounded, largely unit EIS; the present paper adds non-unit EIS, non-EU preferences, attractivity, and matches his rare-disaster solutions at unit EIS.
- **Pohl–Schmedders–Wilms (2024, RFS):** Jensen-bound existence/non-existence; explicitly non-nested with the present conditions for EZ.
- **Dynamic-programming strand** (Le Van–Vailakis, Martins-da-Rocha–Vailakis, Bloise–Vailakis, Balbus, Ren–Stachurski, Bloise–Le Van–Vailakis 2024): distinguished carefully — e.g., Du's fixed-point theorem (used by Ren–Stachurski) needs nonempty interior of the positive cone, which L¹(δ) lacks, motivating the different toolkit.

## Comments
- **Strengths:** (i) Genuine breadth — one set of order-theoretic conditions covering EZ, smooth ambiguity, multiple priors, and robust control with unbounded consumption; no prior paper covers this span. (ii) The lower-perimeter uniqueness argument is elegant and simpler than spectral-radius-of-subgradient alternatives, and yields global attractivity for free — practically valuable for computation. (iii) Conditions are economically interpretable (adjusted growth M(C)/C vs. β-thresholds) and collapse to one-line parameter tests in each application. (iv) The unit-vs-non-unit EIS dichotomy (multiplicity possible at unit EIS; uniqueness within the separable class otherwise) is a clean, memorable takeaway, and the new log-quadratic Bansal–Yaron solution and the smooth-ambiguity uniqueness result under Ju–Miao are concrete contributions. (v) Non-existence results are rare in this literature and here come close to matching the sufficient conditions.
- **Weaknesses / concerns:** (i) **Uniqueness is cone-relative.** All uniqueness claims live in K(C), and the paper's own examples show fixed points outside K(C) can proliferate (the deterministic example after Prop. 12; the V(λ) continuum of Remark 10). Whether restricting to utilities comparable to consumption is economically innocuous is asserted, not proven — a model could admit a non-comparable utility that a planner or asset-pricing model would still use. The title's "uniqueness" should be read with this qualifier. (ii) In the flagship rare-disaster application with EIS > 1, the paper's uniqueness condition *fails* (inf h = 0) and only uniqueness of the separable utility is established; possible non-separable multiplicity — with indeterminate pricing implications — is left open. The workhorse models of asset pricing are exactly where the results are weakest. (iii) Existence conditions are sufficient, not necessary; there is an uncharted gap between Props. 3/5 and 13/14. (iv) Order concavity (needed for uniqueness) restricts risk/ambiguity parameters (s, η ≤ 1 in the applications), excluding some preference regions. (v) Consumption is exogenous; the motivating claim about "indeterminate asset-pricing implications" is never developed quantitatively — no prices or welfare comparisons across the multiple utilities are computed. (vi) The applications verify conditions rather than derive new economics; the non-existence counterfactuals (5%, 8.3%, 15.5% growth changes) are illustrative and somewhat ad hoc.
- **Suggestions:** (1) Prove that under additional primitive assumptions every "admissible" fixed point must lie in K(C) — or give an axiomatic/economic justification for the comparability restriction; this is the natural referee question the paper answers only by example. (2) Compute the asset-pricing implications of the two unit-EIS separable utilities in the Bansal–Yaron and rare-disaster cases (e.g., price–dividend ratios under U⁽⁰⁾ vs U⁽¹⁾) to show multiplicity matters quantitatively. (3) Explore whether tail conditions (inf h over large-H sets, or eventual bounds) can rescue uniqueness when inf h = 0, since unbounded state spaces with adverse tails are the norm in disaster models. (4) Clarify the boundary cases between existence and non-existence (can the gap be closed for homogeneous M?). (5) Exploit global attractivity to provide convergence-rate/error bounds and a practical algorithm, which would raise the paper's profile with the computational macro-finance audience. (6) Tighten the exposition: the Markov section reads at times as a verification of a "conjecture" (separability, §4.2), and the switch between equivalence classes and functions (L¹(δ) vs 𝓛¹(δ)) could be streamlined.

## Possible Publication Venues
1. **Journal of Economic Theory — strong fit.** Direct lineage: Christensen (2022), Bidder–Smith (2018), Marinacci–Montrucchio (2010), Bloise–Vailakis (2018) all appeared in JET; theory-first paper with applications as illustrations of scope.
2. **Journal of Mathematical Economics — strong fit.** Order-theoretic machinery (Kantorovich, Krasnosel'skii, Thompson metric, cone geometry) paired with substantive economics is exactly the journal's profile.
3. **Mathematics of Operations Research — plausible.** The fixed-point toolkit builds on the authors' own MOR paper (unique Tarski fixed points, 2019), though the economic framing, calibrations, and macro-finance applications sit outside typical MOR scope.
4. **Econometrica — stretch.** Adjacent work has landed there (Hansen–Scheinkman 2009; Bloise–Le Van–Vailakis 2024), but this paper's contribution is breadth and a clever proof technique over sufficient-only conditions, with the sharpest uniqueness claims restricted to cones and the separable class — likely viewed as a very good JET paper rather than a conceptual breakthrough.

## Tags
#recursive-utility #unbounded-consumption #non-expected-utility #fixed-points #order-theory #epstein-zin #macro-finance #ambiguity
