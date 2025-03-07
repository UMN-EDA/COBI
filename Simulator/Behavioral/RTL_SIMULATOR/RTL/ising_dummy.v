`timescale 1ns / 1ps
module Ising_Array_50x50 ( 
    output            FREQ_OUT,
    input             PRE_CHARGE_ENB,
    input             ROSC_GLOBAL_EN,
    input             SAMPLE,
    input             SHIL_WEIGHT_ENB,
    input             WEIGHT_ENB,

    input  [199:0]    WBL,      
    input  [49:0]     WWL,      
    output [183:0]    RBLH,   
    input  [49:0]     RWLH,         

    output reg [349:0] SPIN_OUT,

    input  [49:0]    RWLV,     
    output reg [183:0] RBLV      
);

    reg [4:0] sample_count;
    reg       sample_first;

    reg [203:0] memory_h [50:0];
    reg [203:0] memory_v [50:0];    


    reg FREQ_OUT_reg;
    always begin
        FREQ_OUT_reg = ~FREQ_OUT_reg;
        #15;
    end

    initial begin
        $readmemh("./txt/data_1_h.txt", memory_h);
        $readmemh("./txt/data_1_v.txt", memory_v);
        FREQ_OUT_reg   = 0;
        sample_count   = 0;
        sample_first   = 0;
    end

    assign FREQ_OUT = FREQ_OUT_reg & ROSC_GLOBAL_EN;



    reg [5:0] decoder_RWLH;  

    always @(*) begin
        integer i;
        decoder_RWLH = 6'b0;
        for (i = 0; i < 51; i = i + 1) begin
            if (RWLH[i] == 1'b1) begin
                decoder_RWLH = i[5:0];
            end
        end
    end
    assign RBLH = memory_h[decoder_RWLH];

    reg [5:0] decoder_RWLV;  
    integer i;
    always @(*) begin
        decoder_RWLV = 6'b0;
        for (i = 0; i < 51; i = i + 1) begin
            if (RWLV[i] == 1'b1) begin
                decoder_RWLV = i[5:0];
            end
        end
    end
    assign RBLV = memory_v[decoder_RWLV];


    always @(posedge SAMPLE) begin
        if (sample_first != 1) begin
            sample_count = 0;
            sample_first = 1;
        end
        
        sample_count = sample_count + 1;
        if (sample_count == 1) begin
            SPIN_OUT = 350'b1111111111111100000000000000111111111111111111111111111111111111111111111111111111111111111111111100000000000000000000011111111111111111111111111110000000111111100000000000000111111100000001111111111111100000000000000111111100000001111111111111100000000000000111111111111110000000;
        end
        else begin
            SPIN_OUT = {$urandom(),$urandom(),$urandom(),$urandom(), $urandom(),$urandom(),$urandom(),$urandom(),$urandom(),$urandom(), $urandom(),$urandom()};
        end
    end

endmodule
