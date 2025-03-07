module cmp (
input   logic                       clk,
input   logic                       resetb,
input   logic  signed  [`ENERGY_WIDTH:0]   hamiltonian_energy,
input   logic   [`DATA_WIDTH-1:0]   max_fails,
input   logic                       cal_done,
input   logic                       done_ack,
input   logic   [`NUM_ROW-1:0]      save_spin_array,
output  logic   [`NUM_ROW-1:0]      best_spin,
output  logic   [`ENERGY_WIDTH:0]   best_hamiltonian,
output  logic                       done
);
logic [`NUM_ROW-1:0] best_spin_r;
logic [`ENERGY_WIDTH:0] best_hamiltonian_r;
localparam energy_width = `ENERGY_WIDTH + 1;
logic ack, done_reg;
// init an array to energy
logic   signed [`ENERGY_WIDTH:0]      temp_min, temp_min_d;
logic   [`DATA_WIDTH-1:0] count;
logic   save, save_reg;
logic   save_energy;
DW01_cmp2 #(energy_width) u_cmp2 (
.A (hamiltonian_energy),
.B (temp_min),
.TC (1'b1),
.LEQ(1'b0),
.LT_LE(save),
.GE_GT(save_energy)
);

    

always_ff @(posedge clk, negedge resetb)
  if(!resetb) 
    done_reg <= 1'b0;
  else if(max_fails == count && max_fails != 'd0)
    done_reg <= 1'b1;
  else
    done_reg <= 1'b0;

// ack is the posedge detect signal for done_ack
logic ack_r, ack_r1;
always_ff @(posedge clk, negedge resetb)
  if(!resetb) begin
    ack_r <= 1'b0;
    ack_r1 <= 1'b0;
  end
  else begin 
    ack_r <= done_ack;
    ack_r1 <= ack_r;
  end
assign ack = ack_r && !ack_r1;

always_latch begin
  if(!resetb)
     done <= 1'b0;
  else begin
      if(done_reg)
          done <= 1'b1;
      else if(ack)
          done <= 1'b0;
  end
end

always_ff @(posedge clk, negedge resetb) begin
    if(!resetb)
        save_reg <= 1'b0;
    else if (save && cal_done)
        save_reg <= 1'b1;
    else
        save_reg <= 1'b0;
end

always_ff @(posedge clk, negedge resetb) begin
    if(!resetb)
        count <= 'd0;
    else begin
        if(!done && cal_done)
            count <= count + 1'b1;
        else if (save_reg || done)
            count <= 'd0;
        else
            count <= count;
    end
end

always_ff @(posedge clk, negedge resetb) begin
    if(!resetb)
        temp_min <= 'h3FFF;
    else begin
        if (!save && !done)
            temp_min <= temp_min;
        else if (save && !done && cal_done)
            temp_min <= hamiltonian_energy;
        else if(done)
            temp_min <= 'h3FFF;
        else
            temp_min <= temp_min;
    end
end

always_ff @(posedge clk, negedge resetb) begin
    if(!resetb)
        best_spin_r <= 'd0;
    else begin
        if(save_reg)
            best_spin_r <= save_spin_array;
        else
            best_spin_r <= best_spin_r;
    end
end

logic enable;

always@(posedge clk or negedge resetb) begin
    if(!resetb)
	temp_min_d <= 'd0;
    else 
	temp_min_d <= temp_min;
end

assign enable = done_reg && save_energy;
always_ff @(posedge clk, negedge resetb) begin
  if(!resetb) begin
      best_hamiltonian <= 'd0;
      best_spin <= 'd0;
  end else if(enable) begin
      best_hamiltonian <= temp_min_d;
      best_spin <= best_spin_r;
  end
  else begin
      best_hamiltonian <= best_hamiltonian;
      best_spin <= best_spin;
  end
end


endmodule
