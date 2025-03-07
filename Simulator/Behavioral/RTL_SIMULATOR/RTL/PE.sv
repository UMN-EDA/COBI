module acc_calculator (
input  logic 		[`ARRAY_SIZE - 5:0]						spins,		
input  logic				  		                      	clk,
input  logic						                      	sample_trig,	
input  logic						                       	resetb,
input  logic                                                cal_H,
input  logic                                                done_detect,
input  logic                                                step,
input  logic                                                array_done,
input  logic                                                comp,
input  logic                                                save,
input  logic                                                add_weight,
input  logic		[`WORD_WIDTH*(`ARRAY_SIZE-4)-1:0]       row_weight,	            // J in row
input  logic        [`WORD_WIDTH*(`ARRAY_SIZE-4)-1:0]       col_weight,             // J in col
input  logic		[$clog2(`NUM_ROW-1)-1:0]		        row_number,	            // which row do we read
input  logic                                                split,
input  logic                                                stop_sig,
input  logic                                                bypass,
output logic                                                cal_done,                // signal for edge_detect, means H is finish calculated
output logic        [`NUM_ROW-1:0]                          save_spin_array,
output logic        [`ENERGY_WIDTH:0]                       hamiltonian_energy_out
);


localparam  ham_width = $clog2(`ARRAY_SIZE*`ARRAY_SIZE) + `WORD_WIDTH;
logic               [`GREDIENT_SUM_WIDTH:0]                 row_sum, col_sum;
logic	    	    [`NUM_ROW-1:0]			                current_spin_array;		// current spin value
logic               [`NUM_ROW-1:0]                          ori_spin_array;
logic	    	    [$clog2(`NUM_ROW)-1:0]	                current_spin_pointer;					
logic				                                        current_spin;
logic               [(`ARRAY_SIZE-4)*`WORD_WIDTH/2-1:0]     half_row_product;        // half row;
logic               [(`ARRAY_SIZE-4)*`WORD_WIDTH/2-1:0]     half_col_product;
logic	    	    [`NUM_ROW-1:0]			                current_spin_array_split;  
logic               [`WORD_WIDTH*(`ARRAY_SIZE-4)-1:0]       row_weight_split; 
logic               [`WORD_WIDTH*(`ARRAY_SIZE-4)-1:0]       col_weight_split;
logic               [`GREDIENT_SUM_WIDTH:0]                 sum_half_one, sum_half_two;
logic               [`GREDIENT_SUM_WIDTH:0]                 sum_whole;


// First time, the current_spin_array should be the output from ising core
// Then the current_spin_array is the spin after flip
always_ff @(posedge clk, negedge resetb) begin
    if(!resetb)
        ori_spin_array <=  'd0;
    else if (sample_trig)
        ori_spin_array <= spins;
    else
        ori_spin_array <= ori_spin_array;
end

    assign current_spin_array = (!done_detect || bypass) ? ori_spin_array : save_spin_array;
	assign current_spin_pointer = row_number;
	assign current_spin = current_spin_array[current_spin_pointer]; 

// Calculator

    logic   [(`ARRAY_SIZE-4)/2-1:0] spins_half;
    logic   [`WORD_WIDTH*(`ARRAY_SIZE-4)/2-1:0] weight_row_half;
    logic   [`WORD_WIDTH*(`ARRAY_SIZE-4)/2-1:0] weight_col_half;

    always_ff @(posedge clk, negedge resetb) begin
         if(!resetb) begin
            current_spin_array_split <='d0;
            row_weight_split <= 'd0;
            col_weight_split <= 'd0;
        end
        else if(split) begin
            if (cal_H && !bypass) begin
                current_spin_array_split <= save_spin_array;
                row_weight_split <= row_weight;
                col_weight_split <= col_weight;
            end
            else begin
                current_spin_array_split <= current_spin_array;
                row_weight_split <= row_weight;
                col_weight_split <= col_weight;
            end
        end
        else begin
            current_spin_array_split <= current_spin_array;
            row_weight_split <= 'd0;
            col_weight_split <= 'd0;
        end
    end       
// If "STOP", calculate H

    signed_adder 
    signed_half_adder_first (
    .addend_one(row_sum),
    .addend_two(col_sum),
    .enable(comp),
    .signed_sum_delay(sum_half_one),
    .resetb(resetb),
    .clk(clk)
    );

    signed_adder 
    signed_half_adder_second (
    .addend_one(row_sum),
    .addend_two(col_sum),
    .enable(comp),
    .signed_sum(sum_half_two),
    .resetb(resetb),
    .clk(clk)
    );
   
    signed_adder 
    signed_adder_whole (
    .addend_one(sum_half_two),
    .addend_two(sum_half_one),
    .resetb(resetb),
    .clk(clk),
    .enable(add_weight),
    .signed_sum(sum_whole)
    );

   
    vector_splitter_spin 
    row_spin_splitter (  
    .in_vector(current_spin_array_split),                                                         
    .step(step),
    .out_vector(spins_half)
    );

    vector_splitter 
    row_weight_splitter (
    .in_vector(row_weight_split),
    .step(step),
    .out_vector(weight_row_half)
    );

    vector_splitter 
    col_weight_splitter (
    .in_vector(col_weight_split),
    .step(step),
    .out_vector(weight_col_half)
    );

    vector_multiplier col_vector_multipiler (
    .weight_vector(weight_col_half),
    .spin_vector(spins_half),
    .product_vector(half_col_product)
    );

    vector_multiplier row_vector_multiplier (
    .weight_vector(weight_row_half),
    .spin_vector(spins_half),
    .product_vector(half_row_product)
    );
    
    vector_reduce_adder #(.layers_per_clock(7)) 
    row_adder (
    .inVector(half_row_product),
    .current_spin(1'b0),
    .clk(clk),
    .sum(row_sum)
    );

    vector_reduce_adder #(.layers_per_clock(7))
    col_adder (
    .inVector(half_col_product),
    .current_spin(1'b0),
    .clk(clk),
    .sum(col_sum)
    );


// Flip the spin, save the spin & goto next step

// flip the spin or not
logic   new_current_spin;
always_comb begin
    if(!resetb)
        new_current_spin = 1'b0;
    else if (save) begin
        if(  (sum_whole[`GREDIENT_SUM_WIDTH] == 1'b0  && current_spin == 1'b0) || (sum_whole[`GREDIENT_SUM_WIDTH] == 1'b1 && current_spin == 1'b1))
            new_current_spin = !current_spin;
        else
            new_current_spin = current_spin;
    end
end
// save/update the spin
always_ff @(posedge clk, negedge resetb) begin
    if(!resetb)
        save_spin_array <= 'd0;
    else if (sample_trig || bypass)
        save_spin_array <= current_spin_array;
    else if(save && !cal_H)
        save_spin_array[current_spin_pointer] <= new_current_spin;
    else 
        save_spin_array <= save_spin_array;
end

// Calculate hamiltonian energy
logic [`ENERGY_WIDTH:0] sign_bit;
assign sign_bit = sum_whole[`GREDIENT_SUM_WIDTH] == 1'b0 ? 16'b1 : 'b1111111111111111;
logic [`ENERGY_WIDTH:0] hamiltonian_energy;
always_ff @(posedge clk, negedge resetb) begin
    if(!resetb)
        hamiltonian_energy <= 'd0;
    else if (cal_H) begin
        if (save_spin_array[current_spin_pointer] == 0)
            hamiltonian_energy <= hamiltonian_energy+ 16'(sign_bit*abs_sum_whole(sum_whole));
        else
            hamiltonian_energy <= hamiltonian_energy- 16'(sign_bit*abs_sum_whole(sum_whole));
    end
    else if(array_done || sample_trig || stop_sig) begin
        hamiltonian_energy <= 'd0;
    end
    else begin
        hamiltonian_energy <= hamiltonian_energy;
    end
end

always_ff @(posedge clk, negedge resetb) begin
    if(!resetb)
        cal_done <= 1'b0;
    else if(array_done && cal_H)
        cal_done <= 1'b1;
    else
        cal_done <= 1'b0;
end

logic [`ENERGY_WIDTH:0] ori_hamiltonian_energy;
always_ff @(posedge clk, negedge resetb) begin
    if(!resetb)
        ori_hamiltonian_energy <= 'd0;
    else if (cal_H) begin
        if (ori_spin_array[current_spin_pointer] == 0)
            ori_hamiltonian_energy <= ori_hamiltonian_energy+16'(sign_bit*abs_sum_whole(sum_whole));
        else
            ori_hamiltonian_energy <= ori_hamiltonian_energy-16'(sign_bit*abs_sum_whole(sum_whole));
    end
    else if(array_done || sample_trig || stop_sig) begin
        ori_hamiltonian_energy <= 'd0;
    end
    else begin
        ori_hamiltonian_energy <= ori_hamiltonian_energy;
    end
end

assign hamiltonian_energy_out = (bypass == 1'b1) ? ori_hamiltonian_energy: hamiltonian_energy;

// find abs
function [`GREDIENT_SUM_WIDTH:0] abs_sum_whole(
  input [`GREDIENT_SUM_WIDTH:0] sum_whole
  );
begin
  abs_sum_whole = sum_whole[`GREDIENT_SUM_WIDTH] == 1'b0 ? sum_whole[`GREDIENT_SUM_WIDTH:0] : ~sum_whole[`GREDIENT_SUM_WIDTH:0] + 1'b1;
end
endfunction


endmodule


