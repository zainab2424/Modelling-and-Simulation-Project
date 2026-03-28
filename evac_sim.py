import argparse
from sim.experiment import run_experiment, run_experiment_matrix


def main():
    ap = argparse.ArgumentParser(
        description="Apartment Fire Evacuation Monte Carlo Simulation"
    )

    # ===============================
    # Standard Single Experiment Mode
    # ===============================
    ap.add_argument("--runs", type=int, default=100,
                    help="Number of Monte Carlo runs")

    ap.add_argument("--floors", type=int, default=5,
                    help="Number of floors")

    ap.add_argument("--apts", type=int, default=5,
                    help="Apartments per floor")

    ap.add_argument("--stairs", type=int, default=2,
                    help="Number of stairwells")

    ap.add_argument("--occ", type=int, default=2,
                    help="Occupants per apartment")

    ap.add_argument("--time_limit", type=int, default=1000,
                    help="Maximum simulation time steps")

    ap.add_argument("--seed", type=int, default=12345,
                    help="Base random seed")

    # ===============================
    # Matrix Experiment Mode
    # ===============================
    ap.add_argument("--matrix", action="store_true",
                    help="Run structured experiment matrix")

    ap.add_argument("--floor_list", nargs="+", type=int,
                    help="List of floor values for matrix mode")

    ap.add_argument("--stair_list", nargs="+", type=int,
                    help="List of stairwell values for matrix mode")

    ap.add_argument("--occ_list", nargs="+", type=int,
                    help="List of occupancy values for matrix mode")

    args = ap.parse_args()

    # ===============================
    # MATRIX MODE
    # ===============================
    if args.matrix:
        if not (args.floor_list and args.stair_list and args.occ_list):
            raise ValueError(
                "Matrix mode requires --floor_list, --stair_list, and --occ_list"
            )

        run_experiment_matrix(
            runs=args.runs,
            floor_list=args.floor_list,
            stair_list=args.stair_list,
            occ_list=args.occ_list,
            time_limit=args.time_limit,
            base_seed=args.seed,
            apts_per_floor=args.apts,
        )

    # ===============================
    # NORMAL MODE
    # ===============================
    else:
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