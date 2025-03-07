module ICG (
input   logic       ROSC_NODE,
input   logic       ROSC_EN,
input   logic       axi_clk,
input   logic       resetb,
output  logic       FREQ_OUT
);

logic FREQ_OUT_fi;
 CKLNQD1  lat 
 (  .E(ROSC_EN),
    .TE(1'b0),
    .CP(ROSC_NODE),
    .Q(FREQ_OUT_fi)
    );

// avoid X 
logic enable;
always_ff @(posedge axi_clk, negedge resetb)
  if(!resetb)
    enable <= 'b0;
  else if (ROSC_EN)
    enable <= 1'b1;
  else
    enable <= 1'b0;

assign FREQ_OUT = (enable)? FREQ_OUT_fi : 1'b0;
endmodule

