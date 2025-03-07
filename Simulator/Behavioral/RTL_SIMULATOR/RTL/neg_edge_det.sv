module sample_edge_detect (
        input   logic                     clk,
        input   logic                     resetb,
        input   logic                     signal,
        input   logic                     cal_done,
        input   logic [`DATA_WIDTH-1:0]   delay,
        output  logic                     stop,
        output  logic                     address_enable,
        output  logic                     sample_trig_out);

 logic  sig_r0,sig_r1;
 logic  first_sample, first_sample_out, sampled_once;
 logic  sample_trig, sample_trig_delay;

 always_ff @(posedge clk, negedge resetb) begin
    if(!resetb) begin
        sampled_once <= 1'b0;
        first_sample <= 1'b1;
    end
    else if(sig_r1 && ~sig_r0 && !sampled_once) begin
        first_sample <= 1'b0;
        sampled_once <= 1'b1;
    end
    else if (sampled_once) begin
        first_sample <= 1'b1;
    end
    else begin
        first_sample <= first_sample;
        sampled_once <= sampled_once;
    end    
end

 always_ff @(posedge clk, negedge resetb)
  begin
      if(!resetb) begin
		   sig_r0 <= 1'b0;
		   sig_r1 <= 1'b0;
		end
	  else begin
		   sig_r0 <= signal;
		   sig_r1 <= sig_r0;
		end
  end

 always_comb begin
    if(!resetb)
        stop = 1'b0;
    else
        if(!sampled_once)
            stop = 1'b0;
        else
            stop = sig_r1 & ~sig_r0;
 end
 
 always_ff @(posedge clk, negedge resetb) begin
    if (!resetb) begin
        sample_trig <= 1'b0;
    end
    else begin
        if (!first_sample_out) begin
            sample_trig <= 1'b1;
        end
        else if (cal_done) begin
            sample_trig <= 1'b1;
        end
        else begin
            sample_trig <= 1'b0;
        end
    end
 end

always_ff @(posedge clk, negedge resetb) begin
    if(!resetb) begin
        sample_trig_delay <= 1'b0;
    end
    else begin
        sample_trig_delay <= sample_trig;
    end
end

always_ff @(posedge clk, negedge resetb) begin
    if(!resetb) begin
        sample_trig_out <= 1'b0;
    end
    else begin
        sample_trig_out <= sample_trig + sample_trig_delay;
    end
end

pulse_delay u_first_sample_delay
(
.clk            (clk),
.resetb          (resetb),
.first_sample   (first_sample),
.delay          (delay),
.address_enable (address_enable),
.pulse_out      (first_sample_out)
);

endmodule


module pulse_delay (
input  logic         clk,
input  logic         resetb,
input  logic         first_sample,
input  logic [15:0]  delay,
output logic         address_enable,
output logic         pulse_out
);

logic [15:0] counter;
logic pulse_detected;
always @(posedge clk, negedge resetb) begin
    if (!resetb) begin
        pulse_out <= 1'b1;
        counter <= 16'b0;
        pulse_detected <= 1'b0;
    end else if (pulse_detected) begin
        if (counter == delay) begin
            pulse_out <= 1'b0;
            pulse_detected <= 1'b0;
            counter <= 16'b0;
        end else begin
            pulse_out <= 1'b1;
            counter <= counter + 1'b1;
        end
    end else if (!first_sample) begin 
        pulse_detected <= 1'b1;
        counter <= 16'b0;
    end else begin
        pulse_out <= 1'b1;
    end
end

always_ff @(posedge clk, negedge resetb) begin
    if (!resetb) 
        address_enable <= 1'b0;
    else begin
        if (!pulse_detected && ~pulse_out)
            address_enable  <= 1'b1;
        else
            address_enable <= address_enable;
    end
end

endmodule
