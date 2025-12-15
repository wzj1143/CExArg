# CExArg — Contrastive Explanations for Abstract Argumentation

CExArg is a solver-based prototype system for computing **contrastive explanations (CEs)** in abstract argumentation frameworks (AFs).
The system operationalizes the framework developed in the thesis *“Contrastive Explanations in Abstract Argumentation.”*

Given an AF, a **fact** and a **foil**, CExArg identifies a minimal set of modifications to the attack relation that makes the foil accepted, and constructs a CE capturing commonality, difference, and counterfactual edits.

---

## 1. Overview

### Input
- An abstract argumentation framework (APX format)
- A **fact** argument and a **foil** argument
- A semantics (`admissible`, `complete`, `preferred`, `stable`)
- Optional constraints

### Output
A **contrastive explanation** of the form:

CE = (C_∩, C_p, C_q, C_δ)

where:
- C_∩: arguments common to factual and counterfactual witnesses  
- C_p: arguments specific to the factual witness  
- C_q: arguments specific to the counterfactual witness  
- C_δ: a minimal counterfactual edit set (attack additions/removals)

---

## 2. Repository Structure

CE/
├── af_io.py  
├── aspartix_solver.py  
├── min_edit_solver.py  
├── ce_builder.py  
├── main.py  
├── helpers/  
├── semantics/  
├── data/  
├── test/  
├── results/  
├── requirements.txt  
└── README.md  

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

### Minimal Example

```bash
python main.py   --apx data/instances/A-1-BA_40_80_5.apx   --fact a10   --foil a0   --semantics stable
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
- ASP-based semantic reasoning (ASPARTIX + clingo)
- MaxSAT-based minimal editing (RC2 + CEGAR)
- Structured CE construction

---

## 6. Experiments

Experimental scripts are located in `test/`.
Results are written to `results/` and visualized using helper plotting utilities.

If you want to run the automated experiments, you can use the auto_test script provided in the test/ directory.
### Example

```bash
python test/auto_test.py --apx data/instances/A-1-BA_40_80_5.apx
```
### Optional Arguments
- `--n_trials` (default: 10)

---

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
