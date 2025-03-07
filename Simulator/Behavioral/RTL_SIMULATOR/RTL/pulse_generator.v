`timescale 1ns / 1ps

module sync_pulse (
    input   logic       clk_fast,
    input   logic       clk_slow,
    input   logic       rstn,
    input   logic       fast_pulse,
    
    output  logic       slow_sync_ack,
    output  logic       slow_pulse
);

logic   fast_sync_req;
logic   slow_pulse_r1, slow_pulse_r2, req_reg;

logic ack_reg, ack_r1;

// pulse
always_ff @(posedge clk_fast, negedge rstn)
    if(!rstn)
        fast_sync_req <= 1'b0;
    else if(fast_pulse)
        fast_sync_req <= 1'b1;
    else if (slow_sync_ack)
        fast_sync_req <= 1'b0;
    else
        fast_sync_req <= fast_sync_req;

// sample pulse
always_ff @(posedge clk_slow, negedge rstn)
    if(!rstn) begin
        slow_pulse_r1 <= 1'b0;
        slow_pulse_r2 <= 1'b0;
        req_reg <= 1'b0;
    end else begin
        req_reg <= fast_sync_req;
        slow_pulse_r1 <= req_reg;
        slow_pulse_r2 <= slow_pulse_r1;
    end

// handshake
always_ff @(posedge clk_fast, negedge rstn)
    if(!rstn) begin
        ack_r1 <= 1'b0;
        ack_reg <= 1'b0;
    end
    else begin
        ack_reg <= slow_pulse_r1;
        ack_r1 <= ack_reg;
    end
assign slow_sync_ack = ack_r1;
assign slow_pulse = slow_pulse_r1 & (!slow_pulse_r2);

endmodule
