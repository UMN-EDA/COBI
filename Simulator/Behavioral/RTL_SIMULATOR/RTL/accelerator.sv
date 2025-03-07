module accelerator (
input   logic                                         clk,
input   logic                                         sample,
input   logic                                         resetb,
input   logic       [`DATA_WIDTH-1:0]                 max_fails,
input   logic                                         bypass,
input   logic                                         done_ack, 
input   logic       [`ARRAY_SIZE - 5:0]               spins,
input   logic       [`WORD_WIDTH*(`ARRAY_SIZE-4)-1:0] row_weight,
input   logic       [`WORD_WIDTH*(`ARRAY_SIZE-4)-1:0] col_weight,
input   logic       [`DATA_WIDTH-1:0]                 delay,

output  logic       [`NUM_ROW-1:0]                    save_spin_array, 
output  logic       [$clog2(`NUM_ROW-1)-1:0]          row_number,
output  logic       [`ENERGY_WIDTH:0]                 best_hamiltonian,
output  logic       [`NUM_ROW-1:0]                    best_spin,
output  logic                                         address_enable,
output  logic					      prechargeb,
output  logic                                         done
);
logic [`ENERGY_WIDTH:0] hamiltonian_energy;


sample_edge_detect u_sample_edge_detect (
.delay(delay),
.clk(clk),
.resetb(resetb),
.signal(sample),
.stop(stop),
.cal_done(cal_done),
.address_enable(address_enable),
.sample_trig_out(sample_trig)
);

//debug port
logic [2:0] state;
acc_controller u_controller (
.clk(clk),
.resetb(resetb),
.address_enable(address_enable),
.sample_trig(sample_trig),
.cal_done(cal_done),
.stop(stop),
.row_number(row_number),
.cal_H(cal_H),
.done_detect(done_detect),
.step(step),
.array_done(array_done),
.comp(comp),
.save(save),
.add_weight(add_weight),
.split(split),
.stop_out(stop_sig),
.prechargeb(prechargeb),
.state(state)
);

acc_calculator u_calculator (
.spins(spins),
.clk(clk),
.bypass(bypass),
.sample_trig(sample_trig),
.resetb(resetb),
.cal_H(cal_H),
.done_detect(done_detect),
.step(step),
.array_done(array_done),
.comp(comp),
.save(save),
.add_weight(add_weight),
.row_weight(row_weight),
.col_weight(col_weight),
.row_number(row_number),
.split(split),
.stop_sig(stop_sig),
.cal_done(cal_done),
.save_spin_array(save_spin_array),
.hamiltonian_energy_out(hamiltonian_energy)
);

cmp u_cmp (
.clk(clk),
.resetb(resetb),
.hamiltonian_energy(hamiltonian_energy),
.save_spin_array(save_spin_array),
.done_ack(done_ack),
.max_fails(max_fails),
.cal_done(cal_done),
.best_spin(best_spin),
.best_hamiltonian(best_hamiltonian),
.done(done)
);

endmodule
