module convertor
(
	input  [$clog2(`ARRAY_SIZE)-1:0] row_address,
	input  [`ARRAY_SIZE*`WORD_WIDTH-1:0] row_weights,
	input  [`ARRAY_SIZE-1:0]  spins,
	output [$clog2(`ARRAY_SIZE)-1:0] row_address_mem,
	output [183:0] accelerator_mem,
	output [`ARRAY_SIZE-5:0] accelerator_spins
);
	assign row_address_mem = (row_address < (`ARRAY_SIZE-4)/2+1) ? (row_address + 1) : (row_address + 3);
    assign accelerator_mem[183:96] = row_weights[195:108];
    assign accelerator_mem[95:0] = row_weights[99:4];

	assign accelerator_spins[`SHIL-2:0] = spins[`SHIL-1:1];
	assign accelerator_spins[`ARRAY_SIZE-5:`SHIL-1] = spins[`ARRAY_SIZE-2:`SHIL+2]; 
endmodule
