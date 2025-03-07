// Note: Every time change M_COUNT, need to motified the code
module round_robin_arbiter (
   input logic  clk,
   input logic  resetb,
   input logic  detected,

   input logic  [`M_COUNT-1:0] req_i,
   output logic [`M_COUNT-1:0] gnt_o
);

// mask to identify last grant
logic [`M_COUNT-1:0] mask_q,nxt_mask;


always_ff @(posedge clk, negedge resetb)
    if(!resetb)
        mask_q <= 2'b11;
    else if (detected)
        mask_q <= nxt_mask;

// Next mask based on current grant
// Need to parameterize
always_comb begin
    nxt_mask = mask_q;
    if(gnt_o[0])        nxt_mask = 2'b10;
    else if(gnt_o[1])   nxt_mask = 2'b00;
end

logic [`M_COUNT-1:0] mask_req,mask_gnt,raw_gnt;
assign mask_req = req_i & mask_q;

fixed_arbiter  maskedGnt (.req_i(mask_req), .gnt_o(mask_gnt));
fixed_arbiter  rawGnt    (.req_i(req_i), .gnt_o(raw_gnt));

assign gnt_o = |mask_req ? mask_gnt : raw_gnt;

endmodule

