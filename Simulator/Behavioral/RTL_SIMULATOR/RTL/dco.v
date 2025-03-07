`timescale 1ns/1ps

module dco_buf_stage(A,Y);
   parameter stage_num = 14;
   input A;
   output Y;

   wire [stage_num:0] int_net;

   assign int_net[0] = A;
   assign #(0.2) Y          = int_net[stage_num];    // add 200ps for simulation
   //assign #(0.2) Y          = int_net[stage_num];    // add 200ps for simulation

   genvar i;
   generate
      for(i=0; i<stage_num; i=i+1) begin
	 CKBD1  ibuf (.I(int_net[i]), .Z(int_net[i+1]));
      end
   endgenerate
endmodule // dco_buf_stage

module dco_buf_6stage(A,Y);
   parameter stage_num = 6;
   input A;
   output Y;

   wire [stage_num:0] int_net;

   assign int_net[0] = A;
   assign #(0.086) Y          = int_net[stage_num];    // add 100ps for simulation
   //assign #(0.2) Y          = int_net[stage_num];    // add 100ps for simulation

   genvar i;
   generate
      for(i=0; i<stage_num; i=i+1) begin
	 CKBD1  ibuf (.I(int_net[i]), .Z(int_net[i+1]));
      end
   endgenerate
endmodule // dco_buf_6stage

module dco_buf_28stage(A,Y);
   parameter stage_num = 28;
   input A;
   output Y;

   wire [stage_num:0] int_net;

   assign int_net[0] = A;
   assign #(0.4) Y          = int_net[stage_num];    // add 100ps for simulation
   //assign #(0.2) Y          = int_net[stage_num];    // add 100ps for simulation

   genvar i;
   generate
      for(i=0; i<stage_num; i=i+1) begin
	 CKBD1  ibuf (.I(int_net[i]), .Z(int_net[i+1]));
      end
   endgenerate
endmodule // dco_buf_6stage

module dco_top(cnf_coarse, clk_en, clk_out, net_1);
   input [3:0] cnf_coarse;
   input       clk_en;
   output      clk_out;
   output      net_1;

   wire	       clk_out;
   wire [15:0] buf_stage;  // [0] : slowest, [15] : fastest
   wire [7:0]  mux_stage_0;
   wire [3:0]  mux_stage_1;
   wire [1:0]  mux_stage_2;
   wire [0:0]  mux_stage_3;   
   
   // chain part
   genvar      i;

   generate

      for(i=0; i<9; i= i+1) begin
	 dco_buf_6stage ibuf_stage_2(.A(buf_stage[i]), .Y(buf_stage[i+1]));
      end
   endgenerate

   generate

      for(i=9; i<12; i= i+1) begin
	 dco_buf_stage ibuf_stage_3(.A(buf_stage[i]), .Y(buf_stage[i+1]));
      end
   endgenerate

   generate

       for(i=12; i<15; i= i+1) begin
	  dco_buf_28stage ibuf_stage_4(.A(buf_stage[i]), .Y(buf_stage[i+1]));
       end
    endgenerate

   // mux part
   // 1) cnf_coarse[0] x8
   generate
      for(i=0; i<8; i=i+1) begin
	 CKMUX2D0  imux_stage_0_(.I0(buf_stage[2*i+1]), // slow
					 .I1(buf_stage[2*i]),   // fast
					 .S(cnf_coarse[0]),
					 .Z(mux_stage_0[i])
					 );
      end
   endgenerate
   
   // 2) cnf_coarse[1] x4
   generate
      for(i=0; i<4; i=i+1) begin
	 CKMUX2D0  imux_stage_1_(.I0(mux_stage_0[2*i+1]), // slow
					 .I1(mux_stage_0[2*i]),   // fast
					 .S(cnf_coarse[1]),
					 .Z(mux_stage_1[i])
					 );
      end      
   endgenerate

   // 3) cnf_coarse[2] x2
   generate
      for(i=0; i<2; i=i+1) begin
	 CKMUX2D0  imux_stage_2_(.I0(mux_stage_1[2*i+1]), // slow
					 .I1(mux_stage_1[2*i]),   // fast
					 .S(cnf_coarse[2]),
					 .Z(mux_stage_2[i])
					 );
      end      
   endgenerate

   CKMUX2D0  imux_stage_3_(.I0(mux_stage_2[1]),      // slow
				      .I1(mux_stage_2[0]),   // fast
				      .S(cnf_coarse[3]),
				      .Z(mux_stage_3)
				      );

   wire net_1, net_cp, net_cp1, net_cp2;
   CKBD1  ibuf_1 (.I(mux_stage_3), .Z(net_1));
   CKND1  iinv_2 (.I(net_1),       .ZN(net_cp));

   CKLNQD1  iclk_lat (.E(clk_en), .TE(1'b0), .CP(net_cp), .Q(clk_out));    
   CKND1  iinv_3 (.I(net_cp),      .ZN(net_cp1));

   CKND2D1  inand_clk(.A1(clk_en), .A2(net_cp1), .ZN(net_cp2));
   //CKND2D1  inand_clk(.A1(1'b1), .A2(net_cp1), .ZN(net_cp2));    // dco always on, 08.24
   CKBD1  ibuf_st(.I(net_cp2), .Z(buf_stage_pre));

   dco_buf_stage ibuf_stage1(.A(buf_stage_pre), .Y(buf_stage[0]));

endmodule // dco_top

module CKBD1  (input I, output Z);
    assign Z = I;
endmodule

module CKLNQD1  (input TE, E, CP, output reg Q);
    always @(posedge CP)
        if (E || TE)
            Q <= 1'b1;
        else
            Q <= 1'b0;
endmodule

module CKMUX2D0  (input I0, I1, S, output Z);
    assign Z = S ? I1 : I0;
endmodule

module CKND1  (input I, output ZN);
    assign ZN = ~I;
endmodule

module CKND2D1  (input A1, A2, output ZN);
    assign ZN = ~(A1 & A2);
endmodule
