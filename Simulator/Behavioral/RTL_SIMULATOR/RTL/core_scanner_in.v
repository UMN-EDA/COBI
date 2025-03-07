`timescale 1ns / 1ps

module core_scanner_in 
(
    input clk,
    input resetb,

    input s_valid,
    output s_ready,
    input s_last,
    input [`DATA_WIDTH_IN_STREAM - 1 : 0] s_data,
    input logic [`M_COUNT-1:0] access_core,

    output [`M_COUNT - 1 : 0] m_valid,
    input [`M_COUNT - 1 : 0] m_ready,
    output [`M_COUNT - 1 : 0] m_last,
    output logic detected,
    output [`M_COUNT * `DATA_WIDTH_IN_STREAM - 1 : 0] m_data
);

    reg [1:0] c_state;
    //reg tran_ready;
    localparam CORE_NUM = $clog2(`M_COUNT); // number of bits needed to represend number of M_COUNT in binary
    reg [CORE_NUM - 1 : 0 ] index,initial_index; // current core looking at

    localparam ST_SCAN = 2'b01;
    localparam ST_WAIT = 2'b10;
    localparam ST_DONE = 2'b11;
    localparam ST_TRAN = 2'b00;
    logic flag;

    wire o_scan = (c_state == ST_SCAN);
    wire o_tran = (c_state == ST_TRAN);
    wire o_done = (c_state == ST_DONE);


    reg [`M_COUNT - 1 : 0] valid_strb;
    reg [`M_COUNT - 1 : 0] last_strb;
    reg [`M_COUNT * `DATA_WIDTH_IN_STREAM - 1 : 0] data_strb;

    reg m_valid_reg;
    reg m_last_reg;
    reg [`DATA_WIDTH_IN_STREAM - 1 : 0] m_data_reg;

    assign m_valid = valid_strb & {`M_COUNT{m_valid_reg}};
    assign m_last = last_strb & {`M_COUNT{m_last_reg}};
    assign m_data = data_strb & {`M_COUNT{m_data_reg}};   
    
    assign s_ready = ((o_tran | o_done) && m_ready[initial_index]);

    always @ (posedge clk, negedge resetb) begin
        if (!resetb) begin
            c_state <= ST_SCAN;
            m_valid_reg <= 'b0;
            m_last_reg <= 'b0;
            m_data_reg <= 'd0;
            flag <= 1'b0;
            //tran_ready <= 1'b0;
            valid_strb <= 'd0;
            last_strb <= 'd0;
            data_strb <= 'd0; //{M_COUNT{`DATA_WIDTH_IN_STREAM{1'b0}}}; 
	    initial_index <= 'd0; 

        end else begin
            case (c_state)
                ST_TRAN: begin
                    flag <= 1'b0;
                    // everything ready transmit
                    if (s_last && s_valid && s_ready) begin
                        c_state <= ST_DONE;                                   
                        
                        m_valid_reg <= s_valid;
                        m_last_reg <= s_last;
                        m_data_reg <= s_data; 

                    end else if (s_ready) begin
                        c_state <= ST_TRAN;

                        m_valid_reg <= s_valid;
                        m_last_reg <= s_last;
                        m_data_reg <= s_data;                        
                        
                    end

                    
                    // transmit not ready 
                end

                ST_DONE: begin
                    flag <= 1'b0;
                    // 1 cycle delay before scanning again to clear things
                    c_state <= ST_WAIT;
                    valid_strb <= {`M_COUNT{1'b0}};
                    last_strb <= {`M_COUNT{1'b0}};
                    data_strb <= 'd0;   
                    m_valid_reg <= s_valid;
                    m_last_reg <= s_last;
                    m_data_reg <= s_data;
                    
                end

                ST_WAIT: begin
                    flag <= 1'b0;
                    if (s_ready == 1'b0) begin
                        c_state <= ST_SCAN;
                    end
                end

                ST_SCAN: begin
                    flag <= 1'b1;
                    if (m_ready[index] == 1'b1) begin
                        c_state <= ST_TRAN;
                        initial_index <= index;
                        valid_strb <= access_core;
                        last_strb <= access_core;
                        data_strb <= {`DATA_WIDTH_IN_STREAM{1'b1}}<<(`DATA_WIDTH_IN_STREAM*index);

                    end

                    if (s_ready) begin
                        m_valid_reg <= s_valid;
                        m_last_reg <= s_last;
                        m_data_reg <= s_data;
                    end
                end

                default: begin
                    flag <= 1'b0;
                    c_state <= ST_SCAN;
                    if (s_ready) begin
                        m_valid_reg <= s_valid;
                        m_last_reg <= s_last;
                        m_data_reg <= s_data;
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
