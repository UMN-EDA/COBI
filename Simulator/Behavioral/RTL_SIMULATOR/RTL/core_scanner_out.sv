`timescale 1ns / 1ps

module core_scanner_out (
    input clk,
    input resetb,
    
    input [`M_COUNT - 1 : 0] s_valid,
    input [`M_COUNT - 1 : 0] access_core, // core that is available
    output [`M_COUNT - 1 : 0] s_ready,
    input [`M_COUNT - 1 : 0] s_last,
    input [`M_COUNT * `DATA_WIDTH_OUT_STREAM - 1 : 0] s_data,

    output m_valid,
    input m_ready,
    output m_last,
    output logic detected,
    output [`DATA_WIDTH_OUT_STREAM - 1 : 0] m_data
);

    reg [1:0] c_state;
    logic flag;

    localparam ST_SCAN = 2'b01;
    localparam ST_DONE = 2'b11;
    localparam ST_TRAN = 2'b00;
    localparam CORE_NUM = $clog2(`M_COUNT);

    wire o_tran = (c_state == ST_TRAN);
    wire o_done = (c_state == ST_DONE);

    reg [CORE_NUM - 1 : 0] index,initial_index;
    reg [`M_COUNT - 1 : 0] ready_strb;
    wire s_ready_temp;

    reg m_valid_reg;
    reg m_last_reg;
    reg [`DATA_WIDTH_OUT_STREAM - 1 : 0] m_data_reg;
    assign m_valid = m_valid_reg;
    assign m_last = m_last_reg;
    assign m_data = m_data_reg;

    assign s_ready_temp = ~m_valid || m_ready;
    assign s_ready = ready_strb & {`M_COUNT{s_ready_temp}};

    always @ (posedge clk, negedge resetb) begin
        if (!resetb) begin
            c_state <= ST_DONE;
            flag <= 1'b0;
            m_valid_reg <= 1'b0;
            initial_index <= 'd0;
            m_last_reg <= 1'b0;
            m_data_reg <= 'd0;
            ready_strb <= 'd0;
        end else begin
            case (c_state)
                ST_TRAN: begin
                    flag <= 1'b0;
                    if (s_last[initial_index] && s_valid[initial_index] && s_ready_temp) begin
                        c_state <= ST_DONE;
                        

                        m_valid_reg <= s_valid[initial_index];
                        m_last_reg <= s_last[initial_index];
                        m_data_reg <= s_data[(initial_index*`DATA_WIDTH_OUT_STREAM) +: (`DATA_WIDTH_OUT_STREAM)];
                    end else if (s_ready_temp) begin
                        c_state <= ST_TRAN;

                        m_valid_reg <= s_valid[initial_index];
                        m_last_reg <= s_last[initial_index];
                        m_data_reg <= s_data[(initial_index*`DATA_WIDTH_OUT_STREAM) +: (`DATA_WIDTH_OUT_STREAM)];
                    end

                end

                ST_DONE: begin
                    flag <= 1'b0;
                    // 1 cycle delay before scanning again
                    if (s_ready_temp) begin
                        c_state <= ST_SCAN;
                        ready_strb <= {`M_COUNT{1'b0}};
                        m_valid_reg <= 1'b0; //s_valid[access_core];
                        m_last_reg <= 1'b0; //s_last[access_core];
                        m_data_reg <= {`DATA_WIDTH_OUT_STREAM{1'b0}}; //s_data[(access_core*`DATA_WIDTH_OUT_STREAM) +: (`DATA_WIDTH_OUT_STREAM)];
                    end
                end

                ST_SCAN: begin
                    flag <= 1'b1;
                    if(s_valid[index] == 1'b1) begin
                        c_state <= ST_TRAN;
                        ready_strb <= access_core; 
                        initial_index <= index;
                        if(s_ready_temp) begin
                            m_valid_reg <= 'd0;
                            m_last_reg <= 'd0;
                            m_data_reg <= 'd0;
                        end
                    end
                end
                default: begin
                    c_state <= ST_SCAN;
                    flag <= 1'b0;
                    if (s_ready_temp) begin
                        m_valid_reg <= 1'b0; //s_valid[access_core];
                        m_last_reg <= 1'b0; //s_last[access_core];
                        m_data_reg <= {`DATA_WIDTH_OUT_STREAM{1'b0}}; //s_data[(access_core*`DATA_WIDTH_OUT_STREAM) +: (`DATA_WIDTH_OUT_STREAM)];
                    end
                end


            endcase
        end
    end

    logic pre_flag;
    always_ff@(posedge clk, negedge resetb) begin
        if(!resetb) begin
            pre_flag <= 1'b0;
            detected <= 1'b0;
        end else begin
            detected <= pre_flag & ~flag;
            pre_flag <= flag;
        end
    end

// convert one-hot to index
always_comb begin
    index = 'd0;
    for(int oh_index = 0; oh_index < `M_COUNT; oh_index ++) begin
        if(access_core[oh_index]) begin
            index = oh_index;
        end
    end
end
endmodule
