`timescale 1ns / 1ps
module top_cobifive (
    input VDD,
    input VSS,
    input clk,
    input resetb,
    
    // INPUT from FPGA
    input logic s_valid,
    output logic s_ready,
    input logic s_last,
    input logic [`DATA_WIDTH_IN_STREAM - 1 : 0] s_data,

    // OUTPUT to FPGA
    output m_valid,
    input m_ready,
    output m_last,
    output logic [`DATA_WIDTH_OUT_STREAM - 1 : 0] m_data

    
);

    // parameter
    localparam M_COUNT = `M_COUNT;

    logic [`M_COUNT - 1 : 0] s_valid_in_stream;
    logic [`M_COUNT - 1 : 0] s_ready_in_stream;
    logic [`M_COUNT - 1 : 0] s_last_in_stream;
    logic [`M_COUNT - 1 : 0] dco_clk;
    logic [`M_COUNT * `DATA_WIDTH_IN_STREAM - 1 : 0] s_data_in_stream;

    logic [`M_COUNT - 1 : 0] m_valid_out_stream;
    logic [`M_COUNT - 1 : 0] m_ready_out_stream;
    logic [`M_COUNT - 1 : 0] m_last_out_stream;
    logic [`M_COUNT * `DATA_WIDTH_OUT_STREAM - 1 : 0] m_data_out_stream;
    logic [`M_COUNT - 1 : 0] access_core_out,access_core_in;

    // INTERFACE WITH CORE
    logic [`M_COUNT - 1 : 0] program_done;
    logic [`M_COUNT - 1 : 0] core_done;
    logic [`M_COUNT - 1 : 0] core_done_pulse;
    logic [`M_COUNT - 1 : 0] done_ack;
    logic [`OUTPUT_REG_SIZE: 0] core_result      [`M_COUNT - 1 : 0];

    logic [`ARRAY_SIZE - 1 : 0] wwl_out          [`M_COUNT - 1 : 0];
    logic [`TOTAL_ARRAY_NUM_BIT - 1 : 0] wbl_out [`M_COUNT - 1 : 0];

    // control signals
    logic [`DATA_WIDTH_IN_STREAM - 1 : 0] sample_time        [`M_COUNT - 1 : 0];
    logic [`DATA_WIDTH_IN_STREAM - 1 : 0] weight_time_off    [`M_COUNT - 1 : 0];
    logic [`DATA_WIDTH_IN_STREAM - 1 : 0] shil_time          [`M_COUNT - 1 : 0];
    logic [`DATA_WIDTH_IN_STREAM - 1 : 0] rosc_time          [`M_COUNT - 1 : 0];
    logic [`DATA_WIDTH_IN_STREAM - 1 : 0] max_fails          [`M_COUNT - 1 : 0];
    logic [`DATA_WIDTH_IN_STREAM - 1 : 0] sample_delay       [`M_COUNT - 1 : 0];
    logic [`DATA_WIDTH_IN_STREAM - 1 : 0] dco_data           [`M_COUNT - 1 : 0];
    logic [`DATA_WIDTH_IN_STREAM - 1 : 0] problem_id_value   [`M_COUNT - 1 : 0];
    logic [`DATA_WIDTH_IN_STREAM - 1 : 0] problem_id_delay   [`M_COUNT - 1 : 0];
    logic [3:0]                           problem_id_out     [`M_COUNT - 1 : 0];
	logic [14:0]                          hamiltonian_result [`M_COUNT - 1 : 0];
	logic [45 : 0] spin_result                               [`M_COUNT - 1 : 0];
    logic [7*(`ARRAY_SIZE)-1:0] spin_out                     [`M_COUNT - 1 : 0];
    logic detected_in, detected_out;

    // input arbiter
    round_robin_arbiter 
    u_input_rr_arbiter (
    .clk(clk),
    .resetb(resetb),
    .detected(detected_in),
    .req_i(s_ready_in_stream),
    .gnt_o(access_core_in)
    );

    top_stream_in top_stream_in_inst (
        .clk(clk),
        .resetb(resetb),
        .s_valid(s_valid),
        .detected(detected_in),
        .access_core_in(access_core_in),
        .s_ready(s_ready),
        .s_last(s_last),
        .s_data(s_data),
        .m_valid(s_valid_in_stream),
        .m_ready(s_ready_in_stream),
        .m_last(s_last_in_stream),
        .m_data(s_data_in_stream)
    );

    genvar i;
    
    generate
        for (i = 0; i < M_COUNT; i = i+1) begin

            always_ff @(posedge clk, negedge resetb) begin
                if(!resetb) begin
                    problem_id_delay[i] <= 'd0;
                end
                else if(program_done[i] == 1'b1) begin
                    problem_id_delay[i] <= problem_id_value[i];
                end
                else if(m_last) begin
                    problem_id_delay[i] <= 'd0;
                end
            end
            assign problem_id_out[i] = problem_id_delay[i][3:0];

            axi_to_core axi_to_core_inst (
                .clk(clk),
                .resetb(resetb),
                .s_valid(s_valid_in_stream[i]),
                .s_ready(s_ready_in_stream[i]),
                .s_last(s_last_in_stream[i]),
                .s_data(s_data_in_stream[i*`DATA_WIDTH_IN_STREAM +: `DATA_WIDTH_IN_STREAM]),
                .core_done(core_done_pulse[i]),
                .program_done(program_done[i]),
                .wwl_out(wwl_out[i]),
                .wbl_out(wbl_out[i]),
                .sample_time(sample_time[i]),
                .weight_time_off(weight_time_off[i]),
                .shil_time(shil_time[i]),
                .rosc_time(rosc_time[i]),
                .max_fails(max_fails[i]),
                .sample_delay(sample_delay[i]),
                .dco_data(dco_data[i]),
                .problem_id(problem_id_value[i])
            );

            sync_pulse pulse_generator_inst (
                .clk_slow(clk),
                .clk_fast(dco_clk[i]),
                .rstn(resetb),
                .fast_pulse(core_done[i]),
                .slow_pulse(core_done_pulse[i]),
                .slow_sync_ack(done_ack[i])
            );

   
        	ising_calculation iarray
        	(
        		.VDD      		    ( VDD    	                ),		// input
        		.VSS      		    ( VSS         	            ),		// input
        		.sample_time      	( sample_time[i]       	    ),		// input
        		.weight_time_off    ( weight_time_off[i]        ),      // input                        
        		.shil_time      	( shil_time[i]  	    	),      // input
                .problem_id         ( problem_id_value[i]       ),
        		.max_fails		    ( max_fails[i]     	        ),      // input
        		.delay   		    ( sample_delay[i]      		),      // input                    
        		.dco_data       	( dco_data[i] 	            ),      // input                           
        		.prog_done  		( program_done[i]           ),      // input        
        		.WBL  			    ( wbl_out[i]       		    ),      // input    
        		.WWL  			    ( wwl_out[i]       		    ),      // input                   
        		.best_hamiltonian	( hamiltonian_result[i]		),      // output  
        		.best_spins   		( spin_result[i]       		),      // output                   
        		.done			    ( core_done[i]             	),   	// output
                .clk                ( dco_clk[i]                ),      // output
                .done_ack           ( done_ack[i]               ),
        		.resetb			    ( resetb	             	),
                .SPIN_OUT           ( spin_out[i]               ),
        		.axi_clk		    ( clk			        	)   	// output
        	);
            core_to_axi core_to_axi_inst (
                 .clk(clk),
                 .resetb(resetb),
                 .program_done(program_done[i]),
                 .core_done(core_done_pulse[i]),
                 .core_result({problem_id_out[i],i[3:0], spin_result[i], hamiltonian_result[i]}),
                 .m_valid(m_valid_out_stream[i]),
                 .m_ready(m_ready_out_stream[i]),
                 .m_last(m_last_out_stream[i]),
                 .m_data(m_data_out_stream[i*`DATA_WIDTH_OUT_STREAM +:`DATA_WIDTH_OUT_STREAM])
              );
        end  
    endgenerate

    round_robin_arbiter 
    u_output_rr_arbiter (
    .clk(clk),
    .resetb(resetb),
    .detected(detected_out),
    .req_i(m_valid_out_stream),
    .gnt_o(access_core_out)
    );

    top_stream_out
    top_stream_out_inst (
        .clk(clk),
        .resetb(resetb),
        .detected(detected_out),
        .access_core_out(access_core_out),
        .s_valid(m_valid_out_stream),
        .s_ready(m_ready_out_stream),
        .s_last(m_last_out_stream),
        .s_data(m_data_out_stream),
        .m_valid(m_valid),
        .m_ready(m_ready),
        .m_last(m_last),
        .m_data(m_data)
    );

endmodule
