`timescale 1ns / 1ps

// Skid buffer for timing closure
// FPGA/ASIC
// Reference : https://github.com/iammituraj/skid_buffer/blob/main/pipe_skid_buffer.sv
//             https://github.com/matbi86/matbi_fpga_season_1/

module skid_buffer #(parameter FIFO_CMD_LENGTH = 1) (
    input wire clk,
    input wire resetb,

    input wire s_valid,
    output wire s_ready,
    input wire [FIFO_CMD_LENGTH - 1 : 0] s_data,

    output wire m_valid,
    input wire m_ready,
    output wire [FIFO_CMD_LENGTH - 1 : 0] m_data
);

// State
localparam PIPE = 1'b0; /* Stage where data is piped out or stored to temp buffer */
localparam SKID = 1'b1; /* Stage where wait after data skid happened */

reg state_reg; // State register
reg [FIFO_CMD_LENGTH-1:0] m_data_reg, m_data_temp_reg; // Data buffer, spare buffer
reg m_valid_reg, m_valid_temp_reg, s_ready_reg; // Valid and ready signals
wire ready; // Pipeline ready signal

assign ready = m_ready || ~m_valid_reg;
assign s_ready = s_ready_reg;
assign m_data = m_data_reg;
assign m_valid = m_valid_reg;

always @ (posedge clk, negedge resetb) begin
    if (!resetb) begin
        state_reg <= PIPE;
        m_data_reg <= 'd0;
        m_data_temp_reg <= 'd0;
        m_valid_reg <= 1'b0;
        m_valid_temp_reg <= 1'b0;
        s_ready_reg <= 1'b0;
    end else begin
        case (state_reg)
            PIPE: begin
                // PIPE data out
                if (ready) begin
                    m_data_reg <= s_data;
                    m_valid_reg <= s_valid;
                    s_ready_reg <= 1'b1;
                    state_reg <= PIPE;
                end else begin
                    m_data_temp_reg <= s_data;
                    m_valid_temp_reg <= s_valid;
                    s_ready_reg <= 1'b0;
                    state_reg <= SKID;
                end
            end

            SKID: begin
                if (ready) begin
                    m_data_reg <= m_data_temp_reg;
                    m_valid_reg <= m_valid_temp_reg;
                    s_ready_reg <= 1'b1;
                    state_reg <= PIPE;
                end

            end
        endcase
    end
end

endmodule
