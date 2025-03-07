`timescale 1ns / 1ps

module axi_to_core (
    input clk,
    input resetb,

    input s_valid,
    output logic s_ready,
    input s_last,
    input [`DATA_WIDTH - 1 : 0] s_data,

    input core_done, // core is done and ready to receive next stream of data
    output reg program_done, // core is programmed and waiting for core done

    output reg [`ARRAY_SIZE - 1 : 0] wwl_out,
    output [`TOTAL_ARRAY_NUM_BIT - 1 : 0] wbl_out,

    // control signals
    output [`DATA_WIDTH - 1 : 0] sample_time,
    output [`DATA_WIDTH - 1 : 0] weight_time_off,
    output [`DATA_WIDTH - 1 : 0] shil_time,
    output [`DATA_WIDTH - 1 : 0] rosc_time,
    output [`DATA_WIDTH - 1 : 0] max_fails,
    output [`DATA_WIDTH - 1 : 0] sample_delay,
    output [`DATA_WIDTH - 1 : 0] dco_data,
    output [`DATA_WIDTH - 1 : 0] problem_id
);

    //localparam NUM_CONTROL = TOTAL_ARRAY_NUM_BIT / DATA_WIDTH + 1; //11
    //localparam TOTAL_ARRAY_NUM_BIT = 4 * ARRAY_SIZE;
    localparam ARRAY_LOG2 = $clog2(`ARRAY_SIZE);
    localparam ARRAY_NUM_BIT_LOG2 = $clog2(`TOTAL_ARRAY_NUM_BIT);
    
    reg [1:0] c_state;
    localparam ST_STREAM_SRAM = 2'b00; // default at ST_STREAM mode it is always looking for s_valid
    localparam ST_STREAM_CONTROL = 2'b01;
    localparam ST_PROG_DONE = 2'b10; 
    localparam ST_WAIT = 2'b11; // wait until CORE is done set program_done back to 0
    
    wire o_stream_sram = (c_state == ST_STREAM_SRAM);
    wire o_stream_control = (c_state == ST_STREAM_CONTROL);
    wire o_prog_done = (c_state == ST_PROG_DONE);
    wire o_wait = (c_state == ST_WAIT);

    // reg/wire for SRAM_WRITE_PULSE generation
    wire sram_write_pulse;
    reg r_write_pulse;
    reg write_pulse_start;
    assign sram_write_pulse = (r_write_pulse == 1'b0) && (write_pulse_start);
    always @ (posedge clk, negedge resetb) begin
        if (!resetb) begin
            r_write_pulse <= 1'b0;
        end else begin
            r_write_pulse <= write_pulse_start;
        end
    end
    reg sram_hold_pulse; // pulse to hold wbl for additional cycle for
                               // possible timing issue (hold time)
    always @ (posedge clk, negedge resetb) begin
        if (!resetb) begin
            sram_hold_pulse <= 1'b0;
        end else begin
            sram_hold_pulse <=  sram_write_pulse;
        end
    end                           
    
    reg [ARRAY_NUM_BIT_LOG2 - 1 : 0] row_counter; // additional DATA_WIDTH to make sure no losing data
    reg [ARRAY_LOG2 - 1 : 0] col_counter;
    reg [$clog2(`NUM_CONTROL) - 1 : 0] control_counter;

	reg [2:0] write_pulse_cnt;

    wire [`ARRAY_SIZE - 1 : 0] wwl_temp;
    reg  [`DATA_WIDTH * `NUM_CONTROL - 1 : 0] wbl_temp;
    reg  [`DATA_WIDTH * `NUM_CONTROL - 1 : 0] wbl_out_temp;

    reg  [`DATA_WIDTH - 1 : 0] control_reg [`NUM_CONTROL-1 : 0];
    assign wwl_temp = 1 << col_counter;
    //assign wwl_out = (write_pulse_start == 1) ? wwl_temp : {ARRAY_SIZE{1'b0}};
    assign wbl_out = (write_pulse_start == 1) ? wbl_out_temp[`TOTAL_ARRAY_NUM_BIT-1:0] : wbl_temp[`TOTAL_ARRAY_NUM_BIT-1:0];

//(sram_hold_pulse == 0) ? wbl_temp[TOTAL_ARRAY_NUM_BIT-1:0] : wbl_out;

    always @(posedge clk, negedge resetb) begin
        if(!resetb)
            s_ready <= 1'b0;
        else begin
            if (program_done == 1'b1)
                s_ready <= 1'b0;
            else
                s_ready <= 1'b1;
        end
    end

    // ***********************************************************************
    // control signal assignment
    // FIX THIS/DOUBLE CHECK TO MATCH THE ACTUAL CONTROL SIGNALS
    assign sample_time = control_reg[0]; // first in LSB
    assign weight_time_off = control_reg[1];
    assign shil_time = control_reg[2];
    assign rosc_time = control_reg[3];
    assign max_fails = control_reg[4];
    assign sample_delay = control_reg[5];
    assign dco_data = control_reg[6];
    assign problem_id = control_reg[7]; // last in MSB

    // ***********************************************************************
    
    integer i;
    // when it sees first s_valid signal it starts STREAMING state until s_last
    always @ (posedge clk, negedge resetb) begin
        if (!resetb) begin
            program_done <= 1'b0;
            row_counter <= 'd0;
            col_counter <= 'd0;
            control_counter <= 'd0;
            write_pulse_start <= 1'b0;
			write_pulse_cnt <= 'd0;
            wbl_temp <= 'd0;
			wbl_out_temp <= 'd0;
            wwl_out <= 'd0;
            for (i = 0; i < `NUM_CONTROL; i=i+1) begin
                control_reg[i] <= 'd0; 
            end
            c_state <= ST_STREAM_SRAM;
        end else begin
            case(c_state)
                ST_STREAM_SRAM: begin // default state starts with everything empty when data is valid it starts to write to SRAM
                    if (s_valid && s_ready) begin
                        wbl_temp[row_counter +: `DATA_WIDTH] <= s_data;

                        if (row_counter == (`DATA_WIDTH*`NUM_CONTROL) - `DATA_WIDTH) begin
                            row_counter <= 0; // next column
							
                            write_pulse_start <= 1'b1;
							write_pulse_cnt <= 'd0;
                            wwl_out <= 'd0;

							wbl_out_temp <= {s_data, wbl_temp[(`DATA_WIDTH*(`NUM_CONTROL-1))-1:0]}; //[TOTAL_ARRAY_NUM_BIT-1:0];
                            if (col_counter == `ARRAY_SIZE-1) begin
                                c_state <= ST_STREAM_CONTROL;
                            end
                            //wbl_temp <= 'd0;
                        end else begin
                            //if (sram_write_pulse) begin
                            //    write_pulse_start <= 1'b0;
                            //    col_counter <= col_counter + 1;
                            //end
                            row_counter <= row_counter + `DATA_WIDTH;
                        end
                    end

					if (write_pulse_start) begin // wbl_out should be having the most updated row value at this point
                        if (write_pulse_cnt == 0) begin // wwl is 1 cycle delayed from wbl has been finialized and ends 1 cycle before wbl
                            wwl_out <=  wwl_temp;
                            write_pulse_start <= 1'b1;
                        end else if (write_pulse_cnt == 2) begin
                            wwl_out <= 'd0;
                            write_pulse_start <= 1'b1;
							col_counter <= col_counter + 1; // next column
						end else if (write_pulse_cnt == 3) begin
							write_pulse_start <= 1'b0; // end of write_pulse 
                        end else begin
                            write_pulse_start <= 1'b1;
                        end

                        write_pulse_cnt <= write_pulse_cnt + 1; // increment write_pulse_cnt every time
						
					end           
                end
 
                ST_STREAM_CONTROL: begin
                    if (s_valid && s_ready) begin
                        control_reg[control_counter] <= s_data;
                        if (s_last) begin
                            c_state <= ST_PROG_DONE;
                            program_done <= 1'b1;
                        end else begin
                            control_counter <= control_counter + 1'b1;
                        end
                    end

					if (write_pulse_start) begin // wbl_out should be having the most updated row value at this point
                        if (write_pulse_cnt == 0) begin // wwl is 1 cycle delayed from wbl has been finialized and ends 1 cycle before wbl
                            wwl_out <= wwl_temp;
                            write_pulse_start <= 1'b1;
                        end else if (write_pulse_cnt == 2) begin
                            wwl_out <= 'd0;
                            write_pulse_start <= 1'b1;
							col_counter <= col_counter + 1; // next column
						end else if (write_pulse_cnt == 3) begin
							write_pulse_start <= 1'b0; // end of write_pulse 
                        end else begin
                            write_pulse_start <= 1'b1;
                        end

                        write_pulse_cnt <= write_pulse_cnt + 1; // increment write_pulse_cnt every time
						
					end       
                end

                ST_PROG_DONE: begin
                    c_state <= ST_WAIT;
                end

                ST_WAIT: begin // wait until core is done and ready to receive program again
                    if (core_done) begin
                        c_state <= ST_STREAM_SRAM;
                        wbl_temp <= 'd0;
						wbl_out_temp <= 'd0;
                        for (i = 0; i < `NUM_CONTROL; i=i+1) begin
                            control_reg[i] <= 'd0; 
                        end
                        program_done <= 1'b0;
                        row_counter <= 'd0;
                        col_counter <= 'd0;
                        control_counter <= 'd0;
                        write_pulse_start <= 1'b0;
						write_pulse_cnt <= 'd0;
                        wwl_out <= 'd0;
                    end
                end

                default: begin
                    c_state <= ST_STREAM_SRAM;
                    wbl_temp <= 'd0;
					wbl_out_temp <= 'd0;
                    for (i = 0; i < `NUM_CONTROL; i=i+1) begin
                        control_reg[i] <= 'd0; 
                    end
                    program_done <= 1'b0;
                    row_counter <= 'd0;
                    col_counter <= 'd0;
                    control_counter <= 'd0;
                    write_pulse_start <= 1'b0;
					write_pulse_cnt <= 'd0;
                    wwl_out <= 'd0;
                end

            endcase

        end
    end

endmodule
