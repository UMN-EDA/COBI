### 1) Running the Behavioral Simulation

A `Makefile` is provided in this directory to facilitate simulation and waveform generation.

#### Available Makefile Targets:

- **Run simulation:**

  ```
  make run
  ```

  This compiles and runs the simulation.

- **Generate waveform:**

  ```
  make gen_wave
  ```

  Wait for about a minute to generate a waveform file (`wave.vcd`) in the `waveform` folder.

- **Open waveform in GTKWave:**

  ```
  make wave
  ```

  This opens GTKWave to view the waveform.

- **Perform verification:**

  ```
  make verif
  ```

  This compares the Hamiltonian energy obtained from the chip with the results from `qbsolve`.

- **Clean up files:**

  ```
  make clean
  ```

  This removes the simulation executable and waveform file.

### 3) Understanding the Waveform Signals

- The module `top_stream_out_inst` contains the AXI-stream interface signals:

  - `m_data`
  - `m_last`
  - `m_valid`

- To view the **best Hamiltonian energy** and **best spins**, navigate to the module:

  ```
  top_circuit_inst → genblk1 → iarray
  ```

  The relevant signals are:

  - `best_hamiltonian[14:0]`
  - `best_spins[45:0]`

### 4) Running Verification

The verification script `random_gen_text_cobifive_ori.py` is located in the `verification` folder.

#### Steps:

1. Modify the input file path on **line 42** to match the graph being tested.

2. Update **line 95** with the spin values obtained from the chip.

3. Run the verification using:

   ```
   make verif
   ```

### 5) Cleanup

Once all tasks are complete, run:

```
make clean
```

This will delete the simulation executable and waveform files.
