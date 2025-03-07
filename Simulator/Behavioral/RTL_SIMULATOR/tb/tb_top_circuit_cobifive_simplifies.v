`timescale 1ns / 1ps

module tb_top_circuit;
  
    localparam DATA_WIDTH_IN_STREAM = 16;
    localparam DATA_WIDTH_OUT_STREAM = 1;

    localparam INPUT_NUMBER	= 1;
    
    reg clk;
    reg resetb;
    
    reg s_valid;
    wire s_ready;
    reg s_last;
    reg [DATA_WIDTH_IN_STREAM - 1: 0] s_data;
    
    wire m_valid;
    reg m_ready;
    wire m_last;
    wire [DATA_WIDTH_OUT_STREAM - 1 : 0] m_data;
    
    // INTERFACE WITH CORE
    //reg next_core;
    wire temp_core_done;

    // s_valid, s_data, s_last control
    reg [5:0] com_counter;
    reg [7:0] sub_com_counter;

    always begin
        clk = ~clk;
        #2;
    end
    reg [207:0] com_data         [51:0]; //52x52
    reg [207:0] com_data_1       [91:0]; //52x52
	string file_name;
    reg [203:0] data_selected    [51:0];
    reg [183:0] data_selected_rd [91:0];

    reg [183:0] data_selected_rd_0 [91:0];    
    reg [183:0] data_selected_rd_1 [91:0];
    reg [183:0] data_selected_rd_2 [91:0];
    reg [183:0] data_selected_rd_3 [91:0];
    reg [183:0] data_selected_rd_4 [91:0];

    reg	[2  :0]	samp_f0, samp_f1, samp_f2, samp_f3, samp_f4;

    reg [  7:0] num, num_1;
    reg		flag;
    integer i,j;

    //counter for how many input problems will be given
    reg  [10:0] cnt_input;
    reg	 [85:0] m_reg;


    reg results_wr;
    reg results_row_rd;
    reg results_col_rd;



    //-----initial block for writing-----// 
    initial begin
    $display("Starting simulation...");
    $dumpfile("./waveform/wave.vcd");
    $dumpvars(0, tb_top_circuit);
    clk		= 1'b0;
	flag		= 0;
	cnt_input	= 0;
	results_wr	= 0;
	results_row_rd	= 0;
	results_col_rd	= 0;
	num 		= 0;

	samp_f0		= 0;
	samp_f1		= 0;
	samp_f2		= 0;
	samp_f3		= 0;
	samp_f4		= 0;

        #10
        resetb		= 1'b1;
	#40
	resetb		= 1'b0;
	m_ready		= 1'b1;
	#40
	resetb		= 1'b1;

	for(j = 0; j < INPUT_NUMBER; j = j + 1) begin
		num = 0;

		resetb	= 1'b1;

		//input txt to the chip
		$sformat(file_name, "./txt/data_1.txt", j);

		$readmemh(file_name, com_data);

		for(i = 0; i < 51; i = i + 1) begin
			data_selected[i]	= com_data[i][203:0];
		end


		wait(com_counter == 51);
		wait(m_valid);

	end
    wait(m_last == 1'b1)
	#500
	$finish;
    end



//-------------data transfer from testbench to cobifive---------------//
    always @ (posedge clk) begin
        if (!resetb) begin
            s_valid		<= 1'b0;
            s_last		<= 1'b0;
            s_data		<= 'd0;//com_data[0][15:0];
            sub_com_counter	<= 'd0;
            com_counter		<= 'd0;  
        end else if (com_counter < 51) begin
		if (s_ready) begin
            	if (sub_com_counter < 12) begin
                	s_valid		<= 1'b1;
                	s_data		<= com_data[com_counter][sub_com_counter*DATA_WIDTH_IN_STREAM +: DATA_WIDTH_IN_STREAM];
                	sub_com_counter <= sub_com_counter + 1;
                
            	end else begin
                	sub_com_counter <= 'd0;
                	if (com_counter == 50) begin
                    		s_last	<= 1'b1;           
                            //next_core <= 1'b1;
                	end
                	com_counter <= com_counter + 1;
                	s_valid	<= 1'b1;
                	s_data	<= com_data[com_counter][sub_com_counter*DATA_WIDTH_IN_STREAM +: DATA_WIDTH_IN_STREAM];
            	end
		end

        end  else begin
		if (s_ready) begin
			s_valid	<= 1'b0;
			s_data	<= 'd0;
			s_last	<= 1'b0;
			if(cnt_input < INPUT_NUMBER-1) 
				com_counter <= 0;
			else 
				com_counter <= com_counter;
		end

	end 
           
    end

//---------------serial output data to parallel output data----------------------//
    reg [8:0] z;
    always_ff @(posedge clk, negedge resetb)
      if(!resetb) begin
          m_reg	<= 'd0;
          z 	<= 'd0;
      end
      else begin
          if(m_ready && m_valid) begin
              m_reg[z] 	<= m_data;
              z		<= z+1;
          end 
          if (m_valid == 1'b0) begin
              z 	<= 'd0;
              m_reg 	<= 'd0;
          end
    end

 
    top_cobifive 
      top_circuit_inst (
        .clk	(clk	),
        .resetb	(resetb	),
        .s_valid(s_valid),
        .s_ready(s_ready),
        .s_last	(s_last	),
        .s_data	(s_data	),
        
        .m_valid(m_valid),
        .m_ready(m_ready),
        .m_last	(m_last	),
        .m_data	(m_data	)
    );

endmodule
