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

# Function Arguments

* `initial_events` (Dict[str, tuple]): Initial events at enable pins.
    * **Type:** Dictionary mapping enable pins to a tuple.
    * **Description:** Specifies the initial events applied to the enable pins of the circuit. The events are passed as a tuple of three values: arrival time, transition time, and transition type. Arrival time and transition times are in seconds, and the transition type can be 'r' or 'f' for rise or fall.
* `en2osc` (Dict[str, int]): Map enable pins to RO (Ring Oscillator) indices.
    * **Type:** Dictionary mapping enable pin identifiers to ring oscillator indices.
    * **Description:** Defines the correspondence between enable pins and the indices of ring oscillators within the circuit.
* `netlist_path` (str): Path to the netlist file.
    * **Type:** String.
    * **Description:** Specifies the file path to the netlist representing the connectivity of modules.
* `J` (numpy.ndarray): Coupling matrix.
    * **Type:** NumPy array.
    * **Description:** A matrix representing the coupling strengths between the ring oscillators in the circuit.
* `stopTime` (float): Simulation duration.
    * **Type:** Float.
    * **Description:** The total time duration for which the array simulation will be performed.
* `log` (bool, optional): Enable detailed logging.
    * **Type:** Boolean.
    * **Description:** When set to `True`, enables detailed logging of the simulation process. Defaults to `False`.
    * **Default:** `False`
* `logname` (str, optional): Path to the log file.
    * **Type:** String.
    * **Description:** Specifies the file path where the simulation log will be written. Only used if `log` is set to `True`.
    * **Default:** None

# Return Values

* `best_ham` (float): Best Hamiltonian value.
    * **Type:** Float.
    * **Description:** The lowest (best) Hamiltonian value obtained during the simulation.
* `best_sol` (Dict[int, int]): Solution corresponding to the best Hamiltonian.
    * **Type:** Dictionary mapping spin indices to spin values.
    * **Description:** The spin states of the ring oscillators corresponding to the `best_ham` value.

If detailed logging is disabled, a brief summary is provided in the logfile along with the droid runtime and arguments that are needed to recreate the simulation.