module acc_controller (
    input   logic                           clk,
    input   logic                           resetb,
    input   logic                           sample_trig,
    input   logic                           cal_done,
    input   logic                           stop,
    input   logic                           address_enable,

    output  logic  [$clog2(`NUM_ROW-1)-1:0] row_number,      
    output  logic                           cal_H,
    output  logic                           done_detect,
    output  logic                           step,
    output  logic                           array_done,
    output  logic                           comp,
    output  logic			    prechargeb,	
    output  logic                           save,
    output  logic                           add_weight,
    output  logic                           split,
    output  logic                           stop_out,

    // debug port
    output  logic   [2:0]                   state
);
    logic           [2:0]                   counter;
    logic                                   stop_reg;
    logic	    [1:0]			    cnt_pre;
  
localparam num_row = `NUM_ROW;

always_ff @(posedge clk, negedge resetb) begin
    if(!resetb)
        stop_reg <= 1'b0;
    else if (stop)
        stop_reg <= 1'b1;
    else if (counter == 'd5)
        stop_reg <= 1'b0;
end

// state machine
enum    logic [2:0]  {
                     RESET      = 3'b000,
                     SPLIT      = 3'b001,
                     COMP_FIRST = 3'b010,
                     COMP_SECOND= 3'b011,
                     ADD        = 3'b100,
                     SAVE       = 3'b101,
                     NEXT       = 3'b110,
                     XXX        = 3'bxxx
                    } ps, ns;

always_ff @(posedge clk, negedge resetb) begin
    if(!resetb)
        ps <= RESET;
    else
        ps <= ns;
end

always_comb begin
    case(ps)
        RESET:      begin
                        if(sample_trig||cal_H) ns = SPLIT;
                        else                ns = RESET;
                    end
        SPLIT:      begin  
                        if(counter == 3'd1) ns = COMP_FIRST;
                        else                ns = SPLIT;
                    end
        COMP_FIRST: begin
                        if(counter == 3'd2) ns = COMP_SECOND;
                        else                ns = COMP_FIRST;
                    end
        COMP_SECOND:begin
                        if(counter == 3'd3) ns = ADD;
                        else                ns = COMP_SECOND;
                    end
        ADD:        begin
                        if(counter == 3'd4) ns = SAVE;
                        else                ns = ADD;
                    end
        SAVE:       begin
                        if(counter == 3'd5) ns = SPLIT;
                        else if(stop_reg)   ns = RESET;
                        else                ns = SAVE;
                    end
        default:    begin
                    ns = XXX;
                    end
    endcase
end

always_ff @(posedge clk, negedge resetb) begin
    if(!resetb) begin
        step        <= 1'b0;
        comp        <= 1'b0;
        save        <= 1'b0;
        add_weight  <= 1'b0;
        split       <= 1'b0;
	prechargeb  <= 1'b0;
	cnt_pre	    <= 2'b0;
    end
    else begin
        step        <= 1'b0;
        comp        <= 1'b0;
        save        <= 1'b0;
        add_weight  <= 1'b0;
        split       <= 1'b0;
	prechargeb  <= 1'b0;
	cnt_pre     <= 2'b0;
        case(ns)
          RESET: 
          begin
            step        <= 1'b0;
            comp        <= 1'b0;
            save        <= 1'b0;
            add_weight  <= 1'b0;
            split       <= 1'b0;
	    prechargeb  <= 1'b0;
	    cnt_pre	<= 2'b0;
          end
          SPLIT:
          begin
            step <= 1'b1;
            split<= 1'b1;
	    //cnt_pre     <= cnt_pre + 1;
	    //if(cnt_pre == 1 || cnt_pre == 2)
	    prechargeb  <= 1'b1;
          end
          COMP_FIRST:
          begin
            split<= 1'b1;
            step <= 1'b1;
            comp <= 1'b1;
	    prechargeb  <= 1'b1;
          end
          COMP_SECOND:
          begin
            split<= 1'b1;
            comp <= 1'b1;
            step <= 1'b0;
	    prechargeb  <= 1'b1;
          end
          ADD:
          begin 
            split       <= 1'b1;
            step        <= 1'b0;
            add_weight  <= 1'b1;
            comp        <= 1'b0;
	    prechargeb  <= 1'b1;
          end
          SAVE:
          begin
            split       <= 1'b1;
            add_weight  <= 1'b0;
            step        <= 1'b0;
            save        <= 1'b1;
	    prechargeb  <= 1'b0;
          end
          NEXT:
          begin
            split<= 1'b0;
            save <= 1'b0;
          end
        endcase
    end
end

// control signal counter
always_ff @(posedge clk, negedge resetb) begin
    if(!resetb) 
        counter <= 3'd0;
    else if(sample_trig) 
        counter <= 3'd0;
    else if (counter >= 3'd0 && counter < 3'd5) 
        counter <= counter + 1'b1;
    else if (counter == 3'd5)
        counter <= 3'd0;
    else 
        counter <= counter;
end

// row number
always_ff @(posedge clk, negedge resetb) begin
    if(!resetb)
        row_number <= 0;
    else if (sample_trig || (row_number == num_row-1 && counter == 'd5 ) || stop_out || !address_enable)
        row_number <= 0;
    else if (counter == 'd5)
        row_number <= row_number + 1;
    else 
        row_number <= row_number;
end

assign array_done = (row_number == num_row-1 && counter == 'd5) ? 1'b1 : 1'b0;

always_ff @(posedge clk, negedge resetb) begin
    if(!resetb) 
        done_detect <= 1'b0;
    else if(sample_trig)
        done_detect <= 1'b0;
    else begin
        if(counter == 'd5 && row_number == num_row-1 && !done_detect) 
            done_detect <= 1'b1;
        else
            done_detect <= done_detect;
    end
end
always_ff @(posedge clk, negedge resetb) begin
    if(!resetb)
        cal_H <= 1'b0;
    else begin
        if(stop_reg && counter =='d5 )
            cal_H <= 1'b1;
        else if(sample_trig)
            cal_H <= 1'b0;
        else if(cal_done)
            cal_H <= 1'b0;
        else
            cal_H <= cal_H;
    end
end
logic stop_buffer;
assign stop_buffer = (counter == 'd4 || counter == 'd5) ? stop_reg : 1'b0;
always_ff @(posedge clk, negedge resetb)
  if(!resetb)
      stop_out <= 'b0;
  else
      stop_out <= stop_buffer;

assign state = ps;

endmodule
