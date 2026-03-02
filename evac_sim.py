import argparse
from sim.experiment import run_experiment

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=200)
    ap.add_argument("--floors", type=int, default=10)
    ap.add_argument("--apts", type=int, default=10, help="apartments per floor")
    ap.add_argument("--stairs", type=int, default=2, help="number of stairwells")
    ap.add_argument("--occ", type=int, default=2, help="occupants per apartment")
    ap.add_argument("--time_limit", type=int, default=600)
    ap.add_argument("--seed", type=int, default=12345)
    args = ap.parse_args()

    run_experiment(
        runs=args.runs,
        floors=args.floors,
        apts_per_floor=args.apts,
        stairwells=args.stairs,
        occupants_per_apartment=args.occ,
        time_limit=args.time_limit,
        base_seed=args.seed,
    )

if __name__ == "__main__":
    main()