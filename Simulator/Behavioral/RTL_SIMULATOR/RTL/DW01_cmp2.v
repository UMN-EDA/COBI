// customized version
module DW01_cmp2 #(parameter integer WIDTH = 16) (
    input  [WIDTH-1:0] A, B,
    input  LEQ,   // 1 => LEQ/GT, 0 => LT/GEQ
    input  TC,    // 1 => Two's complement, 0 => Unsigned
    output logic LT_LE,
    output logic GE_GT
);

    logic signed [WIDTH-1:0] A_s, B_s;
    logic unsigned [WIDTH-1:0] A_u, B_u;

    always_comb begin
        if (TC) begin // Signed comparison
            A_s = A;
            B_s = B;
            if (LEQ) begin
                LT_LE = (A_s <= B_s);
                GE_GT = (A_s > B_s);
            end else begin
                LT_LE = (A_s < B_s);
                GE_GT = (A_s >= B_s);
            end
        end else begin // Unsigned comparison
            A_u = A;
            B_u = B;
            if (LEQ) begin
                LT_LE = (A_u <= B_u);
                GE_GT = (A_u > B_u);
            end else begin
                LT_LE = (A_u < B_u);
                GE_GT = (A_u >= B_u);
            end
        end
    end

endmodule