module signed_adder 
(
    input   logic signed [`GREDIENT_SUM_WIDTH:0]  addend_one,
    input   logic signed [`GREDIENT_SUM_WIDTH:0]  addend_two,
    input   logic                                   clk,
    input   logic                                   resetb,
    input   logic                                   enable,
    output  logic signed [`GREDIENT_SUM_WIDTH:0]  signed_sum_delay,
    output  logic signed [`GREDIENT_SUM_WIDTH:0]  signed_sum
);

always_ff @(posedge clk, negedge resetb) begin
    if(!resetb) begin 
        signed_sum <= 'd0;
        signed_sum_delay <= 'd0;
    end
    else if (enable) begin
        signed_sum <= addend_one + addend_two;
        signed_sum_delay   <= signed_sum;
    end
    else begin
        signed_sum <= 'd0;
        signed_sum_delay <= 'd0;
    end
end
endmodule
