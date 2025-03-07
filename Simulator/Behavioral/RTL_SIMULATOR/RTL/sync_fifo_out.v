`timescale 1ns / 1ps

// Sync FIFO for timing closure
// FPGA/ASIC
// Reference : https://github.com/matbi86/matbi_fpga_season_1/

module sync_fifo_out  (
    input clk,
    input resetb,

    input s_valid,
    output s_ready,
    input [`FIFO_CMD_LENGTH_OUT - 1 : 0] s_data,

    output m_valid,
    input m_ready,
    output [`FIFO_CMD_LENGTH_OUT - 1 : 0] m_data
);

    localparam FIFO_DEPTH = `FIFO_DEPTH;
    localparam FIFO_CMD_LENGTH = `FIFO_CMD_LENGTH_OUT;
    localparam FIFO_IN_REG = `FIFO_IN_REG;
    localparam FIFO_OUT_REG = `FIFO_OUT_REG;

    // SKID BUFFER
    wire w_s_valid;
    wire w_s_ready;
	wire w_m_valid;
    wire [`FIFO_CMD_LENGTH_OUT - 1 : 0] w_s_data;

    wire w_m_vaild;
    wire w_m_ready;
    wire [`FIFO_CMD_LENGTH_OUT - 1 : 0] w_m_data;

    wire o_empty;
    wire o_full;

    wire i_hs = w_s_valid & w_s_ready;
    wire o_hs = w_m_valid & w_m_ready;

    reg [`FIFO_LOG2_DEPTH - 1 : 0] wptr, wptr_nxt;
    reg wptr_round, wptr_round_nxt;
    reg [`FIFO_LOG2_DEPTH - 1 : 0] rptr, rptr_nxt;
    reg rptr_round, rptr_round_nxt;
    reg [`FIFO_CMD_LENGTH_OUT - 1 : 0] cmd_fifo[`FIFO_DEPTH - 1 : 0];

    integer i;
    always @ (posedge clk, negedge resetb) begin
        if (!resetb) begin
            wptr <= 0;
            wptr_round <= 0;
            for (i = 0; i < FIFO_DEPTH; i = i+1) begin
                cmd_fifo[i] <= {(FIFO_CMD_LENGTH){1'b0}};
            end
        end else if (i_hs) begin
            cmd_fifo[wptr] <= w_s_data;
            {wptr_round,wptr} <= {wptr_round_nxt,wptr_nxt};
        end
    end

    always @ (*) begin
        if (wptr == (FIFO_DEPTH-1)) begin
            wptr_nxt = 0;
            wptr_round_nxt = ~wptr_round;
        end else begin
            wptr_nxt = wptr + 'd1;
            wptr_round_nxt = wptr_round;
        end
    end

    always @ (posedge clk,negedge resetb) begin
        if (!resetb) begin
            rptr <= 0;
            rptr_round <= 0;
        end else if (o_hs) begin
            {rptr_round,rptr} <= {rptr_round_nxt,rptr_nxt};
        end
    end

    assign w_m_data = cmd_fifo[rptr];

    always @ (*) begin
        if (rptr == (FIFO_DEPTH-1)) begin
            rptr_nxt = 0;
            rptr_round_nxt = ~rptr_round;
        end else begin
            rptr_nxt = rptr + 'd1;
            rptr_round_nxt = rptr_round;
        end
    end

    assign o_empty = (wptr_round == rptr_round) && (wptr == rptr);
    assign o_full = (wptr_round != rptr_round) && (wptr == rptr);

    assign w_s_ready = ~o_full;
    assign w_m_valid = ~o_empty;

    // Generate Skid buffer
    generate
        if (FIFO_IN_REG) begin
            skid_buffer #(.FIFO_CMD_LENGTH(`FIFO_CMD_LENGTH_OUT))
            skid_buffer_out (
                .clk(clk),
                .resetb(resetb),

                .s_valid(s_valid),
                .s_ready(s_ready),
                .s_data(s_data),

                .m_valid(w_s_valid),
                .m_ready(w_s_ready),
                .m_data(w_s_data)
            );
        end else begin
            assign w_s_valid = s_valid;
            assign s_ready = w_s_ready;
            assign w_s_data = s_data;
        end
    endgenerate

    generate
        if (FIFO_OUT_REG) begin
            skid_buffer #(.FIFO_CMD_LENGTH(`FIFO_CMD_LENGTH_OUT)) skid_buffer_out2 (
                .clk(clk),
                .resetb(resetb),

                .s_valid(w_m_valid),
                .s_ready(w_m_ready),
                .s_data(w_m_data),

                .m_valid(m_valid),
                .m_ready(m_ready),
                .m_data(m_data)
            );
        end else begin
            assign m_valid = w_m_valid;
            assign w_m_ready = m_ready;
            assign m_data = w_m_data;
        end
    endgenerate

endmodule
