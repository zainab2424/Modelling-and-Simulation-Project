# Apartment Fire Evacuation Simulation

## Overview

This project simulates apartment building evacuation during a fire using an **agent-based model** and repeated **Monte Carlo experiments**. It compares two behavioral conditions:

- **Calm scenario**: occupants evacuate without panic-related disruption
- **Panic scenario**: occupants may hesitate, freeze, choose worse routes, and create heavier congestion

The project is designed to study how **occupant behavior**, **building layout**, and **fire conditions** affect evacuation performance.

---

## Features

- Agent-based evacuation model
- Multi-floor apartment building generation
- Adjustable floors, apartments, stairwells, and occupancy
- Fire ignition and probabilistic spread
- Hazard-based slowdown and edge blocking
- Panic growth from danger and nearby occupants
- Queueing and congestion on movement paths
- Repeated Monte Carlo runs for scenario comparison
- CSV result export and automatic plot generation
- Optional matrix experiments across multiple building configurations

---

## Project Structure

```text
.
├── evac_sim.py
├── requirements.txt
├── results_runs.csv
├── results_summary.csv
├── experiment_matrix_summary.csv
├── figures/
└── sim/
    ├── __init__.py
    ├── agents.py
    ├── building.py
    ├── experiment.py
    ├── hazard.py
    ├── plots.py
    ├── routing.py
    └── simulation.py
````

---

## Main Files

* `evac_sim.py` — command-line entry point for running experiments
* `sim/building.py` — building graph and movement edges
* `sim/agents.py` — occupant agent definition and generation
* `sim/hazard.py` — fire ignition, danger growth, and spread
* `sim/routing.py` — path and reachability helpers
* `sim/simulation.py` — core evacuation simulation loop
* `sim/experiment.py` — repeated experiments, summaries, and benchmarking
* `sim/plots.py` — result visualization

---

## How the Simulation Works

The building is represented as a directed graph where:

* **nodes** represent apartments, corridors, stairs, and the exit
* **edges** represent allowed movement paths

Each simulation run includes:

1. Generating occupants with randomized reaction time, panic susceptibility, and speed
2. Creating a building layout
3. Igniting a fire at a selected node
4. Updating fire spread and local danger over time
5. Updating occupant panic levels
6. Moving occupants through the building while handling queues and congestion
7. Recording evacuation performance metrics

Each experiment runs many times with different random seeds so results can be compared more reliably.

---

## Metrics Collected

The simulation records metrics such as:

* number evacuated
* number not evacuated
* mean evacuation time
* p90 evacuation time
* maximum queue length
* bottleneck events
* average queue load
* evacuated fraction
* floor clearance time
* panic freeze events
* panic-related bad route choices

---

## Installation

Install the required packages:

```bash
pip install -r requirements.txt
```

Required libraries:

* numpy
* pandas
* matplotlib
* tqdm

---

## Quick Start

Run a standard experiment with:

```bash
python evac_sim.py --runs 100 --floors 5 --apts 5 --stairs 2 --occ 2 --time_limit 600 --seed 42
```

This will:

* build the apartment model
* run calm and panic simulations
* save CSV outputs
* generate plots in the `figures/` folder

---

## Command-Line Arguments

### Standard mode

```bash
python evac_sim.py --runs 200 --floors 10 --apts 10 --stairs 2 --occ 2 --time_limit 600 --seed 12345
```

Arguments:

* `--runs` : number of Monte Carlo runs
* `--floors` : number of floors
* `--apts` : apartments per floor
* `--stairs` : number of stairwells
* `--occ` : occupants per apartment
* `--time_limit` : maximum simulation steps per run
* `--seed` : base random seed

### Matrix mode

```bash
python evac_sim.py --matrix --runs 100 --floor_list 5 10 15 --stair_list 1 2 --occ_list 2 4 --apts 10 --time_limit 600 --seed 12345
```

Matrix mode runs multiple building configurations automatically and stores the combined summary in `experiment_matrix_summary.csv`.

---

## Output Files

* `results_runs.csv` — raw output for every run
* `results_summary.csv` — summary statistics for calm vs panic
* `benchmark_comparison.csv` — comparison against simple reference ranges
* `experiment_matrix_summary.csv` — summary of matrix experiments
* `figures/` — generated visualizations

---

## Assumptions

This model is intentionally simplified. Some key assumptions are:

* one shared corridor per floor
* all occupants start in apartments
* one simulation step is treated approximately as one second
* movement is graph-based rather than full physical navigation
* panic and fire spread are represented using simplified probabilistic rules

---

## Purpose

This project can be used to explore questions such as:

* How much does panic worsen evacuation performance?
* Does adding stairwells reduce congestion?
* How does building height affect evacuation time?
* How does higher occupancy impact bottlenecks and evacuation success?

---

## Summary

This project provides a flexible simulation framework for analyzing apartment fire evacuation under both calm and panic conditions. It combines building layout modelling, individual occupant behavior, fire hazard spread, crowd congestion, and repeated experimentation to produce measurable and comparable results.
