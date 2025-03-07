module ising_calculation 
(
    input   logic   [`DATA_WIDTH-1:0]                                    sample_time,
    input   logic   [`DATA_WIDTH-1:0]                                    weight_time_off,
    input   logic   [`DATA_WIDTH-1:0]                                    shil_time,
    input   logic   [`DATA_WIDTH-1:0]                                    rosc_time,
    input   logic   [`DATA_WIDTH-1:0]                                    max_fails,
    input   logic   [`DATA_WIDTH-1:0]                                    delay,
    input   logic   [`DATA_WIDTH-1:0]                                    dco_data,
    input   logic   [`DATA_WIDTH-1:0]                                    problem_id,
    input   logic                                                        prog_done,
    input   logic   [`ARRAY_SIZE*`WORD_WIDTH-1:0]                        WBL,
    input   logic   [`ARRAY_SIZE-1:0]                                    WWL,
    input   logic                                                        resetb,
    input   logic                                                        axi_clk,
    input   logic                                                        done_ack, 
   

    inout   wire                                                         VDD,
    inout   wire                                                         VSS,
    output  logic   [`ENERGY_WIDTH-1:0]                                  best_hamiltonian,
    output  logic   [`ARRAY_SIZE-5:0]                                    best_spins,
    output  logic   [7*(`ARRAY_SIZE)-1:0]                                SPIN_OUT,
    output  logic                                                        clk,
    output  logic                                                        done

);

logic [`ENERGY_WIDTH:0]                 best_hamiltonian_reg;
logic [`ARRAY_SIZE-5:0]                 accelerator_spins;
logic [`WORD_WIDTH*(`ARRAY_SIZE-4)-1:0] row_weight;
logic [`WORD_WIDTH*(`ARRAY_SIZE-4)-1:0] col_weight;
logic [$clog2(`ARRAY_SIZE)-1:0]         row_number;             // row number in acc
logic [$clog2(`ARRAY_SIZE)-1:0]         row_address_mem;        // row WL to row decoder
logic [$clog2(`ARRAY_SIZE)-1:0]         col_address_mem;        // col WL to col decoder
logic                                   address_enable;
logic [`CORE_SIZE-1:0]                 SPIN;
logic [`WORD_WIDTH*`ARRAY_SIZE-1:0]     RBLH;
logic [`WORD_WIDTH*`ARRAY_SIZE-1:0]     RBLV;
logic [`ARRAY_SIZE-1:0]                 RWLH;
logic [`ARRAY_SIZE-1:0]                 RWLV;
logic                                   bypass;
logic                                   debug_out;                                 
logic                                   SCAN_IN;
logic                                   SCAN_CLK_OUT;
logic                                   SCAN_OUT;
logic                                   fails_reached;
wire                			prechargeb, ROSC;

assign best_hamiltonian = best_hamiltonian_reg >>> 1;


assign bypass = (problem_id[15] == 1'b1) ? 1'b1: 1'b0;

`ifdef CORE
// ising_core
Ising_Array_50x50 u_ising_core
(
.FREQ_OUT       (ROSC_NODE),     // output to controller
.PRE_CHARGE_ENB (prechargeb),   // input from controller
.RBLH           (RBLH),         // output to converter_row
.RBLV           (RBLV),         // output to converter_col
.ROSC_GLOBAL_EN (prog_done),    // input from outside
.RWLH           (RWLH),         // input from decoder_row
.RWLV           (RWLV),         // input from decoder_col
.SAMPLE         (sample),       // input from controller
.SHIL_WEIGHT_ENB(shil_enb),     // input from controller
.SPIN_OUT       (SPIN_OUT),     // output to majority_check
.WEIGHT_ENB     (weight_enb),   // input from controller
.WBL            (WBL),          // input from outside
.WWL            (WWL)           // input from outside
);
majority_check u_majority
(
.SPIN_SAMPLE    ({SCAN_OUT,SPIN_OUT}),   // input from ising_core
.SPIN           (SPIN)                   // output to converter
);

ICG u_ICG
(
.ROSC_EN   (prog_done),
.ROSC_NODE (ROSC_NODE),
.FREQ_OUT  (freq_out),
.resetb    (resetb),
.axi_clk   (axi_clk)
);

decoder u_decoder_row
(
.address_enable (address_enable),       // input from accelerator
.WL_num(row_address_mem),               // input from convertor_row
.prechargeb(prechargeb),
.WL(RWLH)                               // output to ising core
);

decoder  u_decoder_col
(
.address_enable(address_enable),        // input from accelerator
.WL_num(col_address_mem),               // input from convertor row
.prechargeb(prechargeb),
.WL(RWLV)                               // output to ising core
);

convertor u_convertor_row
(
.row_address (row_number),              // input from accelerator
.row_weights(RBLH),                      // input from ising core
.spins(SPIN),                           // input from majority check
.row_address_mem(row_address_mem),      // output to decoder
.accelerator_mem(row_weight),           // output to accelerator
.accelerator_spins(accelerator_spins)   // output to accelerator
);

convertor u_convertor_col
(
.row_address (row_number),              // input from accelerator
.row_weights(RBLV),                      // input from ising core
.row_address_mem(col_address_mem),      // output to decoder
.accelerator_mem(col_weight)            // output to accelerator
);

`else
Ising_Array_50x50 u_ising_core
(
.FREQ_OUT       (freq_out),     // output to controller
.PRE_CHARGE_ENB (prechargeb),   // input from controller
.RBLH           (row_weight),   // output to converter_row
.RBLV           (col_weight),   // output to converter_col
.ROSC_GLOBAL_EN (prog_done),    // input from outside
.RWLH           (RWLH),         // input from decoder_row
.RWLV           (RWLV),         // input from decoder_col
.SAMPLE         (sample),       // input from controller
.SHIL_WEIGHT_ENB(shil_enb),     // input from controller
.SPIN_OUT       (SPIN_OUT),     // output to majority_check
.WEIGHT_ENB     (weight_enb),   // input from controller
.WBL            (WBL),          // input from outside
.WWL            (WWL)           // input from outside
);

majority_check u_majority
(
.SPIN_SAMPLE    ({SCAN_OUT,SPIN_OUT}),   // input from ising_core
.SPIN           (SPIN)                   // output to converter
);

decoder u_decoder_row
(
.address_enable (address_enable),       // input from accelerator
.WL_num(row_number),                    // input from convertor_row
.prechargeb(prechargeb),
.WL(RWLH)                               // output to ising core
);

decoder  u_decoder_col
(
.address_enable(address_enable),        // input from accelerator
.WL_num(row_number),                    // input from convertor row
.prechargeb(prechargeb),
.WL(RWLV)                               // output to ising core
);

`endif

controller u_controller
(
.sample_time        (sample_time),      // input from outside
.weight_time_off    (weight_time_off),  // input from outside
.shil_time          (shil_time),        // input from outside
.prog_done          (prog_done),        // input from outside
.resetb             (resetb),          
.freq_out           (freq_out),         // input from ising_core
.fails_reached      (fails_reached),             // input from accelerator
.weight_enb         (weight_enb),       // output to ising_core
.sample             (sample),           // output to ising_core & accelerator
.shil_enb           (shil_enb)         // output to ising core
//.prechargeb         (prechargeb)        // output to ising_core
);
accelerator u_accelerator
(
.clk                (clk),              // input from dco
.sample             (sample),           // input from controller
.bypass             (bypass),
.resetb             (resetb),            // input from outside(almost),
.max_fails          (max_fails),        // input from outside
.spins              (SPIN),// input from converter
.row_weight         (row_weight),       // input from converter_row
.col_weight         (col_weight),       // input from converter_col
.row_number         (row_number),       // output to converter
.delay              (delay),
.done_ack           (done_ack), 
.address_enable     (address_enable),   // output to decoder
.best_hamiltonian   (best_hamiltonian_reg), // output to outside
.best_spin          (best_spins),       // output to outside
.prechargeb 	    (prechargeb),
.done               (done)              // output to outside & controller
);



logic clk_en;
dco_top u_dco
(
.cnf_coarse (dco_data[3:0]),
.clk_en(clk_en),
.net_1(clk)
);


always_ff @(posedge axi_clk, negedge resetb)
  if(!resetb)
    clk_en <= 'b0;
  else
    clk_en <= prog_done;
endmodule

