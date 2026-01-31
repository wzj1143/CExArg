# CExArg — Contrastive Explanations for Abstract Argumentation

CExArg is a solver-based prototype system for computing **contrastive explanations (CEs)** in abstract argumentation frameworks (AFs).
The system operationalizes the framework developed in the thesis *“Contrastive Explanations in Abstract Argumentation.”*

Given an AF, a **fact** and a **foil**, CExArg identifies a minimal set of modifications to the attack relation that makes the foil accepted, and constructs a CE capturing commonality, difference, and counterfactual edits.

---

## 1. Overview

### Input
- An abstract AF (APX format)
- A **fact** argument and a **foil** argument
- A semantics (`admissible`, `complete`, `preferred`, `stable`)
- Optional constraints

### Output
A **CE** of the form:

CE = (C_∩, C_p, C_q, C_δ)

where:
- C_∩: arguments common to factual and counterfactual witnesses  
- C_p: arguments specific to the factual witness  
- C_q: arguments specific to the counterfactual witness  
- C_δ: a minimal counterfactual edit set (attack additions/removals)

---

## 2. Repository Structure
```text
CE/
├── af_io.py                 # Parsing of APX files and internal AF representation
├── aspartix_solver.py       # Extension computation via ASPARTIX encodings and clingo
├── min_edit_solver.py       # Minimal counterfactual edit sets computation (MaxSAT + CEGAR)
├── ce_builder.py            # Construction and formatting of CEs
├── main.py                  # Command-line interface for computing a CE
│
├── helpers/                 # Auxiliary utilities (validation, plotting...)
├── semantics/               # ASPARTIX semantics encodings (adm, comp, pref, stab)
├── data/
│   └── examples/            # AF used in the thesis examples
├── test/                    # Test scripts (e.g., auto_test)
├── results/                 # Generated CSV files and plots from experiments
│
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
```
---

## 3. Requirements and Installation

The project is implemented in **Python = 3.12**.

All required Python dependencies are listed in `requirements.txt`.
Install them using:

```bash
pip install -r requirements.txt
```
---

## 4. Command-Line Usage
This repository does **not** include the ICCMA 2019 benchmark instances due to licensing and size considerations.  
To run the system on your own data, please place the desired AF files (in APX format) into the `data/` directory.

A CE can then be computed using the following general command:

```bash
python main.py   --apx <path-to-af.apx>  --fact <fact-argument> --foil <foil-argument> --semantics <semantics>
```
### Example

```bash
python main.py   --apx data/examples/ce1.apx   --fact d   --foil e   --semantics preferred
```

### Optional Arguments

- `--edit_mode {add,del,both}` (default: both)
- `--radius <int>` (default: 2)
- `--given_extension`
- `--ce_variant {baseline,keep_fact,status_reversal}` (default: baseline)
- `--max_iters <int>` (default: 10000)
- `--time_budget_sec <float>` (default: None)
- `--verbose` (default: disabled)

---

## 5. Algorithmic Core

CExArg combines:
- AF in/output
- ASP-based semantic reasoning (ASPARTIX + clingo)
- MaxSAT-based minimal editing (RC2 + CEGAR)
- Structured CE construction

---

## 6. Experiments

Experimental scripts are located in `test/`.
Results are written to `result/` and visualized using helper plotting utilities.

If you want to run the automated experiments, you can use the auto_test script provided in the test/ directory.
### Example
single AF
```bash
python test/auto_test.py --apx data/examples/ce1.apx
```
a set of AFs
```bash
python test/auto_test.py --instances_dir data/instances --n_trials 10 --out result/baseline_ce_results.csv
```
### Optional Arguments
- `--n_trials` (default: 10)  # Number of successful CE you want
- `--instances_dir` # Directory of the set of AFs (need to be .apx format)
- `--out`(default: result/baseline_ce_results.csv) # Directory of the result csv file
---
If you want to generate plots
```bash
python helpers/plot.py
```
## 7. Relation to the Thesis

This implementation realizes the **argument-contrast** setting defined in the thesis.

---

## 8. Status and Dependencies

Research prototype for academic use. 

We gratefully acknowledge the following systems, which form the technical backbone of the implementation.

### clingo
- GitHub: https://github.com/potassco/clingo

### ASPARTIX
- Website: https://www.dbai.tuwien.ac.at/research/argumentation/aspartix/

### PySAT
- PySAT GitHub: https://github.com/pysathq/pysat
