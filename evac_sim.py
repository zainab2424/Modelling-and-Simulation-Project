import argparse
from sim.experiment import run_experiment, run_experiment_matrix


def main():
    """
    Main entry point for the simulation program.

    This function:
    1. Creates the command-line argument parser
    2. Defines all supported arguments for both normal mode and matrix mode
    3. Reads the user's command-line input
    4. Decides which experiment function to run based on the arguments provided

    There are two supported execution modes:

    1. Normal mode
       Runs one building configuration many times and compares calm vs panic behavior.

    2. Matrix mode
       Runs multiple building configurations automatically by looping through
       different values for floors, stairwells, and occupancy.

    Example normal mode:
        python evac_sim.py --runs 100 --floors 5 --apts 5 --stairs 2 --occ 2

    Example matrix mode:
        python evac_sim.py --matrix --runs 50 --floor_list 5 10 --stair_list 1 2 --occ_list 2 3
    """

    # Create the argument parser object.
    # This is what allows the program to read values like --runs 100
    # from the terminal when the script is executed.
    ap = argparse.ArgumentParser(
        description="Apartment Fire Evacuation Monte Carlo Simulation"
    )

    # ==========================================================
    # Standard Single Experiment Mode Arguments
    # ==========================================================
    # These arguments control a single simulation configuration.
    # In this mode, the program runs many Monte Carlo trials for
    # one building setup, then compares calm and panic scenarios.

    ap.add_argument(
        "--runs",
        type=int,
        default=100,
        help="Number of Monte Carlo runs"
    )
    # Number of repeated trials to perform.
    # Higher values usually give more stable average results,
    # but they also increase total runtime.

    ap.add_argument(
        "--floors",
        type=int,
        default=5,
        help="Number of floors"
    )
    # Number of floors in the apartment building.

    ap.add_argument(
        "--apts",
        type=int,
        default=5,
        help="Apartments per floor"
    )
    # Number of apartment units on each floor.

    ap.add_argument(
        "--stairs",
        type=int,
        default=2,
        help="Number of stairwells"
    )
    # Number of stairwells available in the building.
    # More stairwells may reduce congestion.

    ap.add_argument(
        "--occ",
        type=int,
        default=2,
        help="Occupants per apartment"
    )
    # Number of people placed inside each apartment at the start
    # of the simulation.

    ap.add_argument(
        "--time_limit",
        type=int,
        default=1000,
        help="Maximum simulation time steps"
    )
    # Maximum number of time steps allowed for one simulation run.
    # If not all agents evacuate before this limit, the run ends anyway.

    ap.add_argument(
        "--seed",
        type=int,
        default=12345,
        help="Base random seed"
    )
    # Starting seed for random number generation.
    # This helps make runs reproducible.
    # Each Monte Carlo run usually uses this base plus an offset.

    # ==========================================================
    # Matrix Experiment Mode Arguments
    # ==========================================================
    # Matrix mode is used when you want to test multiple building
    # configurations automatically in one command.
    #
    # Instead of using just one value for floors, stairs, or occupancy,
    # you can provide lists of values and the code will run all
    # combinations of those settings.

    ap.add_argument(
        "--matrix",
        action="store_true",
        help="Run structured experiment matrix"
    )
    # This is a flag, not a numeric input.
    # If included in the terminal command, matrix mode is turned on.
    #
    # Example:
    #   python evac_sim.py --matrix ...

    ap.add_argument(
        "--floor_list",
        nargs="+",
        type=int,
        help="List of floor values for matrix mode"
    )
    # A list of floor counts to test in matrix mode.
    #
    # Example:
    #   --floor_list 5 10 15

    ap.add_argument(
        "--stair_list",
        nargs="+",
        type=int,
        help="List of stairwell values for matrix mode"
    )
    # A list of stairwell counts to test in matrix mode.
    #
    # Example:
    #   --stair_list 1 2

    ap.add_argument(
        "--occ_list",
        nargs="+",
        type=int,
        help="List of occupancy values for matrix mode"
    )
    # A list of occupant-per-apartment values to test in matrix mode.
    #
    # Example:
    #   --occ_list 2 3 4

    # Read and store all command-line arguments entered by the user.
    # After this line, values can be accessed using args.runs,
    # args.floors, args.matrix, etc.
    args = ap.parse_args()

    # ==========================================================
    # MATRIX MODE
    # ==========================================================
    # If the user included the --matrix flag, the program switches
    # to matrix experiment mode.
    if args.matrix:

        # In matrix mode, the program requires three lists:
        # 1. floor_list
        # 2. stair_list
        # 3. occ_list
        #
        # If any of these are missing, the matrix experiment cannot
        # be created properly, so we stop and raise an error.
        if not (args.floor_list and args.stair_list and args.occ_list):
            raise ValueError(
                "Matrix mode requires --floor_list, --stair_list, and --occ_list"
            )

        # Run the matrix experiment.
        #
        # This function will test multiple combinations of building
        # size and occupancy settings and produce combined summary results.
        run_experiment_matrix(
            runs=args.runs,
            floor_list=args.floor_list,
            stair_list=args.stair_list,
            occ_list=args.occ_list,
            time_limit=args.time_limit,
            base_seed=args.seed,
            apts_per_floor=args.apts,
        )

    # ==========================================================
    # NORMAL MODE
    # ==========================================================
    # If --matrix was not provided, the script runs in standard mode.
    # This means one building configuration is tested repeatedly.
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
        # This function runs the main calm-vs-panic experiment for
        # a single building layout using repeated Monte Carlo trials.


# This makes sure main() only runs when this file is executed directly.
# It will not automatically run if this file is imported into another file.
if __name__ == "__main__":
    main()
