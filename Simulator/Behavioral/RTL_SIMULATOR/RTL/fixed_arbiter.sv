module fixed_arbiter (
    input       wire[`M_COUNT-1:0] req_i,
    output      wire[`M_COUNT-1:0] gnt_o   // One-hot grant signal
);
  localparam NUM_PORTS = `M_COUNT;
  // Port[0] has highest priority
  assign gnt_o[0] = req_i[0];

  genvar i;
  for (i=1; i<NUM_PORTS; i=i+1) begin
    assign gnt_o[i] = req_i[i] & ~(|gnt_o[i-1:0]);
  end

endmodule
