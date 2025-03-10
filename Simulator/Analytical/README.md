This simulator implements DROID: Discrete-Time Simulation for Ring-Oscillator-Based Ising Design ([arXiv:2502.19399](https://arxiv.org/abs/2502.19399)).

To set up the virtual environment required, please use the requirements.txt file.

**Create a virtual environment (recommended):**

    This helps isolate the project's dependencies.

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip3 install -r requirements.txt
    ```
The top-level function is `sim` from `droid.py`. Here is a summary of its arguments and return values:

# Args:
 	`initial_events`: Initial events at enable pins 
 	`en2osc`: Map enable pins to RO indices
 	`netlist_path`: Path to netlist
 	`J`: Coupling matrix
 	`stopTime`: Simulate the array for this duration 
 	`log`: Set to True to Enable detailed logging
 	`logname`: Path to logfile

# Returns:
  `best_ham`: Best Hamiltonian value from the simulation
  `best_sol`: Solution corresponding to the best Hamiltonian


If detailed logging is disabled, a brief summary is provided in the logfile along with the droid runtime and arguments that are needed to recreate the simulation.
