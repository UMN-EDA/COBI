module controller 
(
input logic [`DATA_WIDTH-1:0]    sample_time,
input logic [`DATA_WIDTH-1:0]    weight_time_off,
input logic [`DATA_WIDTH-1:0]	shil_time,
input logic 		   		    prog_done,
input logic      				resetb,
input logic  				    freq_out,
input logic 				    fails_reached,

output  logic 			 	    weight_enb,  
output  logic    		        sample, 
output  logic 				    shil_enb
//output 	logic                   prechargeb 
);


// counter
logic [`DATA_WIDTH-1:0] time_counter;
logic idle_trig;
//assign prechargeb = prog_done;

enum logic [3:0] {RESET  = 4'b0000,
                  IDLE   = 4'b0001,
                  SHIL   = 4'b0010,
                  NOSHIL = 4'b0011,
                  WEIGHT = 4'b0100,
                  NOWEI  = 4'b0101,
                  NOSAW  = 4'b0110,
                  WAIT   = 4'b0111,
                  SAMPLE = 4'b1000
                  } ps, ns;

// counter
always_ff @(posedge freq_out, negedge resetb) begin
  if(!resetb)
      time_counter <= 'd0;
  else if (time_counter == sample_time || !prog_done || idle_trig)
      time_counter <= 'd0;
  else 
      time_counter <= time_counter + 1'b1;
end

always_ff @(posedge freq_out, negedge resetb) begin
  if(!resetb)
      ps <= RESET;
  else
      ps <= ns;
end

always_comb begin
  weight_enb = 1'b0;
  sample = 1'b0;
  shil_enb = 1'b0;
  idle_trig = 1'b0;
  case(ps)
    RESET:
    begin
        weight_enb = 1'b0;
        shil_enb = 1'b0;
        sample = 1'b0;
        if(prog_done)
            ns = IDLE;
        else
            ns = RESET;
    end
    IDLE:
    begin
        idle_trig = 1'b0;
        weight_enb = 1'b1;
        shil_enb = 1'b1;
        if (shil_time == 'd0 && weight_time_off == 'd0)
            ns = NOSAW; 
        else if (weight_time_off == 'd0)
            ns = NOWEI;
        else if (shil_time == 'd0)
            ns = NOSHIL;
        else if (weight_time_off != 'd0 && shil_time != 'd0)
            if ( (time_counter == shil_time) && (time_counter == weight_time_off))
                ns = WEIGHT;
            else if ((time_counter == shil_time))
                ns = SHIL;
            else
                ns = IDLE;
        else
            ns = IDLE;
    end
    NOSAW:
    begin
        if (fails_reached) begin
            ns = RESET;
        end
        idle_trig = 1'b0;
        weight_enb = 1'b1;
        shil_enb = 1'b1;
        ns = WAIT;
    end
    SHIL: 
    begin
        if (fails_reached) begin
            ns = RESET;
        end
 
        idle_trig = 1'b0;
        shil_enb = 1'b0;
        if (weight_time_off == 'd0)
            weight_enb = 1'b1;
        if((time_counter == weight_time_off) && (weight_time_off != 'd0))
            ns = WEIGHT;
        else
            ns = SHIL;
    end
    NOSHIL:
    begin
        if (fails_reached) begin
            ns = RESET;
        end
        idle_trig = 1'b0;
        weight_enb = 1'b1;
        shil_enb = 1'b1;
        if((time_counter == weight_time_off) && (weight_time_off != 'd0))
            ns = WEIGHT;
        else
            ns = NOSHIL;
    end 
    WEIGHT:
    begin
        if (fails_reached) begin
            ns = RESET;
        end
        idle_trig = 1'b0;
        weight_enb = 1'b0;
        if(shil_time == 'd0)
            shil_enb = 1'b1;
        else 
            shil_enb = 1'b0;
        ns = WAIT;
    end
    NOWEI:
    begin
        if (fails_reached) begin
            ns = RESET;
        end
        idle_trig = 1'b0;
        weight_enb = 1'b1;
        ns = WAIT;
    end
    WAIT:
    begin
        idle_trig = 1'b0;
        if (fails_reached) begin
            ns = RESET;
        end
        if (shil_time == 'd0 && weight_time_off == 'd0) begin
            shil_enb = 1'b1;
            weight_enb = 1'b1;
        end
        else if(shil_time == 'd0) begin
            weight_enb = 1'b0;
            shil_enb = 1'b1;
        end
        else if (weight_time_off == 'd0) begin
            weight_enb = 1'b1;
            shil_enb = 1'b0;
        end
        else begin
            weight_enb = 1'b0;
            shil_enb = 1'b0;
        end
        if(time_counter == sample_time)
            ns = SAMPLE;
        else
            ns = WAIT;
    end
    SAMPLE:
    begin
        idle_trig = 1'b0;
        sample = 1'b1;
        if (fails_reached) begin
            ns = RESET;
        end
        if (shil_time == 'd0 && weight_time_off == 'd0) begin
            shil_enb = 1'b1;
            weight_enb = 1'b1;
        end
        else if(shil_time == 'd0) begin
            weight_enb = 1'b0;
            shil_enb = 1'b1;
        end
        else if (weight_time_off == 'd0) begin
            weight_enb = 1'b1;
            shil_enb = 1'b0;
        end
        else begin
            weight_enb = 1'b0;
            shil_enb = 1'b0;
        end
        if(time_counter == 'd5) begin
            idle_trig = 1'b1;
            ns = IDLE;
        end
        else
            ns = SAMPLE;
    end
    default: 
    begin
        sample = 1'bx;
        idle_trig = 1'bx;
        weight_enb = 1'bx;
        shil_enb = 1'bx;
        ns = RESET;
    end
  endcase
end
endmodule        

