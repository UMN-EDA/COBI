
module top_stream_out ( 
    input clk,
    input resetb,

    input [`M_COUNT - 1 : 0] s_valid,
    output [`M_COUNT - 1 : 0] s_ready,
    input [`M_COUNT - 1 : 0] s_last,
    input [`M_COUNT * `DATA_WIDTH_OUT_STREAM - 1 : 0] s_data,
    input [`M_COUNT - 1: 0] access_core_out,
    output detected,
    output m_valid,
    input m_ready,
    output m_last,
    output [`DATA_WIDTH_OUT_STREAM - 1 : 0] m_data
);

    wire valid_sync;
    wire ready_sync;
    wire last_sync;
    wire [`DATA_WIDTH_OUT_STREAM - 1 : 0] data_sync;

    // Sync FIFO and Skid buffer for timing closure
    // between chip and fpga
    sync_fifo_out
    sync_fifo_inst (
        .clk(clk),
        .resetb(resetb),

        .s_valid(valid_sync),
        .s_ready(ready_sync),
        .s_data({last_sync,data_sync}),

        .m_valid(m_valid),
        .m_ready(m_ready),
        .m_data({m_last,m_data})
    );

    core_scanner_out core_scanner_out_inst (
        .clk(clk),
        .resetb(resetb),
        .s_valid(s_valid),
        .detected(detected),
        .access_core(access_core_out),
        .s_ready(s_ready),
        .s_last(s_last),
        .s_data(s_data),
        .m_valid(valid_sync),
        .m_ready(ready_sync),
        .m_last(last_sync),
        .m_data(data_sync)
    );

endmodule
