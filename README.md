# Apartment Fire Evacuation Simulation (Agent-Based + Monte Carlo)

## Install
pip install -r requirements.txt

## Run
python evac_sim.py --runs 200 --floors 10 --apts 10 --stairs 2 --occ 2 --time_limit 600 --seed 12345

## Outputs
- results_runs.csv
- results_summary.csv
- figures/evac_time_hist.png
- figures/p90_boxplot.png
- figures/congestion_boxplot.png