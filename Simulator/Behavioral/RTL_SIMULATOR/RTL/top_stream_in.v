`timescale 1ns / 1ps

module top_stream_in (
    input clk,
    input resetb,

    input s_valid,
    output s_ready,
    input s_last,
    output detected,
    input [`DATA_WIDTH_IN_STREAM - 1 : 0] s_data,
    input [`M_COUNT-1:0] access_core_in,

    output [`M_COUNT - 1 : 0] m_valid,
    input  [`M_COUNT - 1 : 0] m_ready,
    output [`M_COUNT - 1 : 0] m_last,
    output [`M_COUNT * `DATA_WIDTH_IN_STREAM - 1 : 0] m_data
);

    localparam DATA_WIDTH = `DATA_WIDTH_IN_STREAM;
    wire valid_sync;
    wire ready_sync;
    wire last_sync;
    logic m_valid_temp, m_ready_temp, m_last_temp;
    logic [DATA_WIDTH-1:0] m_data_temp;
    wire [DATA_WIDTH - 1 : 0] data_sync;    

    // Sync FIFO and Skid buffer for timing closure
    // between fpga and chip
    sync_fifo_in sync_fifo_inst (
        .clk(clk),
        .resetb(resetb),

        .s_valid(s_valid),
        .s_ready(s_ready),
        .s_data({s_last,s_data}),

        .m_valid(valid_sync),
        .m_ready(ready_sync),
        .m_data({last_sync,data_sync})
    );

    core_scanner_in core_scanner_in_inst (
        .clk(clk),
        .resetb(resetb),
        .access_core(access_core_in),
        .s_valid(valid_sync),
        .s_ready(ready_sync),
        .s_last(last_sync),
        .s_data(data_sync),
        .detected(detected),
        .m_valid(m_valid),
        .m_ready(m_ready),
        .m_last(m_last),
        .m_data(m_data)
    );
    
endmodule
