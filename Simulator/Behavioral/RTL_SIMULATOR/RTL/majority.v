module majority_check 
  (
   input [`ARRAY_SIZE*7:0] SPIN_SAMPLE,
   output wire [`CORE_SIZE-1:0] SPIN
  );
localparam array_size = `CORE_SIZE;
genvar i;
wire [6:0] slice[`CORE_SIZE-1:0]; // Declare an array of wires for the slices

assign slice[0] = SPIN_SAMPLE[6:0]; // Initial value for i=0
generate
   for (i = 1; i < array_size-1; i = i + 1) begin
      assign slice[i] = SPIN_SAMPLE[i*7 +: 7];
   end
endgenerate

genvar j;
generate
   for (j = 0; j < array_size-1; j = j + 1) begin : counter_inst
      counter_7bit inst_counter (
         .SPIN_SAMPLE(slice[j]),
         .SPIN(SPIN[j])
      );
   end
endgenerate

endmodule
   
module counter_7bit(
  input [6:0] SPIN_SAMPLE,
  output wire SPIN
);
  reg [2:0] SPIN_COUNT;
	integer i;
	always @ (SPIN_SAMPLE, SPIN_COUNT) begin
		SPIN_COUNT = 0;
		
		for (i = 0; i < 7; i = i + 1) begin
			if (SPIN_SAMPLE[i] == 1'b1) begin
				SPIN_COUNT = SPIN_COUNT + 1;
			end
		end
   end
   assign SPIN = SPIN_COUNT[2];  // 100, 101, 110, 111 (4,5,6,7)
endmodule
