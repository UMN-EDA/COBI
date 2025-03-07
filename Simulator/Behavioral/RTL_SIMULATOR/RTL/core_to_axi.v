`timescale 1ns / 1ps

module core_to_axi (
    input clk,
    input resetb,
    input program_done,
    input core_done,
    input [`OUTPUT_REG_SIZE - 1 : 0] core_result,
    input debug_out,

    output reg m_valid,
    input m_ready,
    output reg m_last,
    output reg [`DATA_WIDTH_OUT_STREAM - 1 : 0] m_data
);
    reg [1:0] c_state;
    logic     debug_reg;
    localparam ST_IDLE = 2'b00;
    localparam ST_WAIT = 2'b01;
    localparam ST_STREAM = 2'b10;
    localparam ST_DONE = 2'b11;
    localparam OUTPUT_REG_SIZE_LOG2 = $clog2(`OUTPUT_REG_SIZE);

    reg [OUTPUT_REG_SIZE_LOG2 - 1 : 0] result_cnt;
    reg [`OUTPUT_REG_SIZE - 1: 0] core_result_reg;

    always @ (posedge clk, negedge resetb) begin
        if (!resetb) begin
            c_state <= ST_IDLE;
            m_valid <= 1'b0;
            m_last <= 1'b0;
            m_data <= 'd0;
            result_cnt <= 'd0;
			core_result_reg <= 'd0;
        end else begin
            case (c_state)
                ST_IDLE: begin
                    if (program_done) begin
                        c_state <= ST_WAIT;                        
                    end
                end
                ST_WAIT: begin
                    if (core_done) begin
                        core_result_reg <= core_result;
                        c_state <= ST_STREAM;
                        m_valid <= 1'b1;
                        m_data <= core_result[result_cnt*`DATA_WIDTH_OUT_STREAM +: `DATA_WIDTH_OUT_STREAM];
                        m_last <= 1'b0;
                        result_cnt <= result_cnt + 1'b1;
                    end
                end
                ST_STREAM: begin
                    if (m_ready) begin
                        if (result_cnt == `OUTPUT_REG_SIZE-1) begin
                            c_state <= ST_DONE;
                            m_valid <= 1'b1;
                            m_data <= core_result_reg[result_cnt*`DATA_WIDTH_OUT_STREAM +: `DATA_WIDTH_OUT_STREAM];
                            m_last <= 1'b1;
                        end else begin
                            result_cnt <= result_cnt + 1;
                            m_valid <= 1'b1;
                            m_data <= core_result_reg[result_cnt*`DATA_WIDTH_OUT_STREAM +: `DATA_WIDTH_OUT_STREAM];
                        end
                    end
                end
                ST_DONE: begin
                    if (m_ready) begin
                        m_valid <= 1'b0;
                        m_data <= 'd0;
                        m_last <= 1'b0;
                        result_cnt <= 'd0;
                        c_state <= ST_IDLE;
                    end
                end
            endcase
        end
    end


endmodule
