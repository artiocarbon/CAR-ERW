# Enhanced Rock Weathering (ERW) — CAR Curves

This repo ships precomputed results and a small viewer to explore them. Below I document the scientific rationale, the end-to-end procedure, and the data/assumption stack we used to generate the curves. If you want to reproduce, extend, or audit any step, get in touch (contact at the end) and we’ll share more.

## TL;DR 🧭

- We estimate how much CO₂ is durably retained by ERW over time under uncertainty.
- Outputs are CAR curves: for a target confidence (e.g., CAR95), we show the guaranteed retained CO₂ (in kg per tonne promised) as a function of time.
- Results are computed for several stone compositions (A–D) and multiple CAR levels (e.g., 95, 90, 85, 80).
- The viewer lets you overlay multiple stones at one CAR, multiple CARs for one stone, or all combinations, with the mineral composition printed on each plot.

## What’s in this repository 📁

- `results/`: precomputed results (JSON files).
- `app.py`: viewer application (Streamlit).
- `README.md`: this file.

Each JSON contains time series of guarantee curves and the associated CAR percentiles (no model code included).

## How to run ▶️

1 - Clone the repo

```bash
$ git clone https://github.com/your-repo/your-repo.git
$ cd your-repo
```

2 - Install dependencies

```bash
$ pip install -r requirements.txt
```

3 - Run the app

```bash
$ streamlit run app.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501).
Use the sidebar to pick:

Stones (A–D) from results/ (e.g., A_CAR.json, B_CAR.json, …)

CAR levels (95/90/85/80)

View mode (stones@CAR, CARs@stone, or all)

Each plot shows the mineral composition in the bottom-right legend.


## Theoretical framework
- State model: 1-D soil column (∼1 m, layered), monthly steps. Rock is mixed in the top layer. 

- Reaction rate: harmonic mean of (i) a kinetic volumetric rate (lab→field–penalized, temp & pH corrected) and (ii) a supply-limited rate set by advection and equilibrium porewater concentrations.

- Surface & passivation: optional geometric scaling 𝐴∝𝑀 and temporal passivation to reflect evolving reactive area/coatings.

- Carbon accounting (gross): Mass-balanced conversion of reacted moles into ocean alkalinity and soil carbonate fractions (no double counting).

- Normalization: Guarantees reported as kg CO₂ per tonne promised, capped in [0,1000] by stoichiometry.

## CAR definition:

Guaranteed retention at CARX is the (100−X)th percentile across Monte Carlo samples (e.g., CAR95 ⇒ P5).

Carbon At Risk at time 𝑡 is 1000−guarantee(t) (kg per tonne).

## How we produced the results (what’s inside the JSONs) 🔬


- Stone compositions: Each of A–D defines mass fractions over four proxy minerals with distinct kinetics/stoichiometry:
CaSiO₃, MgSiO₃ (2 mol CO₂/mol) and NaAlSi₃O₈, KAlSi₃O₈ (1 mol CO₂/mol).

- Environment: Example set calibrated to a cool, mildly acidic soil regime (Alaska-like climate envelope) for demonstration.

- Uncertainty (MC): We sample field-scale drivers (lab→field penalty, dose, mixing depth, water flux) and run many trajectories to form percentile envelopes over time.

- Outputs: For each stone, we compute guarantee curves at selected CAR levels (95/90/85/80) and store them with the time axis, percentiles, N, horizon, and the exact composition that generated them.


## Caveats & scope 🚧

- Gross CO₂ only, we do not subtract process emissions. In other words, these results exclude a full life-cycle assessment (LCA) of the ERW supply chain.

- Reduced mineral system (4 proxies) and simplified pH coupling for auditability and speed.

- Single-column transport, no lateral heterogeneity.

- Results are composition and environment-dependent; regionalize inputs to move beyond the demo envelope.

## Contact 🤝

Jorge Veiras 
✉️ jorge@artiocarbon.com

## References
 - Maher, K. (2010). The dependence of chemical weathering rates on fluid residence time. Earth and Planetary Science Letters, 294(1–2), 101–110. https://doi.org/10.1016/j.epsl.2010.03.010

 - Maher, K., & Chamberlain, C. P. (2014). Hydrologic regulation of chemical weathering and the geologic carbon cycle. Science, 343(6178), 1502–1504. https://doi.org/10.1126/science.1250770

 - Levy, C. R., Almaraz, M., Beerling, D. J., Raymond, P., Reinhard, C. T., Suhrhoff, T. J., & Taylor, L. (2024). Enhanced Rock Weathering for Carbon Removal–Monitoring and mitigating potential environmental impacts on agricultural land. Environmental Science & Technology, 58(39), 17215–17226. https://doi.org/10.1021/acs.est.4c02368

 - Kantzas, E. P., Martin, M. V., Lomas, M. R., Eufrasio, R. M., Renforth, P., Lewis, A. L., Taylor, L. L., Mecure, J., Pollitt, H., Vercoulen, P. V., Vakilifard, N., Holden, P. B., Edwards, N. R., Koh, L., Pidgeon, N. F., Banwart, S. A., & Beerling, D. J. (2022). Substantial carbon drawdown potential from enhanced rock weathering in the United Kingdom. Nature Geoscience, 15(5), 382–389. https://doi.org/10.1038/s41561-022-00925-2
 