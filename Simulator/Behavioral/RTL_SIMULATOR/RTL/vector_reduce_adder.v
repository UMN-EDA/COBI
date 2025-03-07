//adds all 2's complemnt values in the input vector, returns with set size
// Tag.01 yhhong 23.04.13 realSumWidth error 

module vector_reduce_adder 
#(parameter word_size=4,parameter vector_size=`NUM_ROW/2, parameter sum_size=12, parameter layers_per_clock = -1)(
    input [vector_size*word_size-1:0] inVector,
    input current_spin,
    input clk,
    output [sum_size-1:0] sum
);

//localparam realSumWidth = $clog2(vector_size) + word_size -1;
localparam realSumWidth = $clog2(vector_size) + word_size;   // Tag.01 word_size = sign + mangitude
   
wire [realSumWidth-1:0] realsum;

//sign extension
genvar i;
generate
    for(i=0;i<(sum_size-realSumWidth);i=i+1) assign sum[i+realSumWidth] = realsum[realSumWidth-1];
endgenerate
assign sum[realSumWidth-1:0] = realsum;


vector_adder_tree #(.word_size(word_size),.vector_size(vector_size),.sum_size(realSumWidth),.mem_every(layers_per_clock),.layers_to_mem(layers_per_clock))
    half_tree(.inVector(inVector),.current_spin(current_spin),.clk(clk),.sum(realsum));


endmodule

//tree for adding all values together
module vector_adder_tree
#(parameter word_size=4,parameter vector_size=64, parameter sum_size=14, parameter mem_every=-1,parameter layers_to_mem=-1)(
    input [vector_size*word_size-1:0] inVector,
    input current_spin,
    input clk,
    output [sum_size-1:0] sum
);

generate
if(vector_size ==2)begin 

    wire [sum_size-1:0] sum_unmultiplied;
    assign sum_unmultiplied = inVector[word_size*2-1-:word_size] + inVector[word_size-1-:word_size];
    assign sum = (current_spin)?(-1 * sum_unmultiplied):sum_unmultiplied;

end
else if(layers_to_mem==0) begin
    reg [vector_size*word_size-1:0] mem;
    reg current_spin_mem;
    always @(posedge clk) begin 
        mem <= inVector;
        current_spin_mem <= current_spin;
    end
    vector_adder_tree #(.word_size(word_size),.vector_size(vector_size),.sum_size(sum_size),
    .mem_every(mem_every),.layers_to_mem(mem_every)) nextLayer (.inVector(mem),.current_spin(current_spin_mem), .clk(clk),.sum(sum));
end
else begin : recursive_tree_layers
    localparam next_layer_size = (vector_size/3)*2 + (vector_size%3);
    localparam nex_layers_to_mem = (layers_to_mem<0)?-1:layers_to_mem-1;
    wire [next_layer_size*(word_size+1)-1:0] layer_sum;
    vector_reduction_layer #(.word_size(word_size),.vector_size(vector_size)) layerAdder (.inVector(inVector),.outVector(layer_sum));
    vector_adder_tree #(.word_size(word_size+1),.vector_size(next_layer_size),.sum_size(sum_size),
    .mem_every(mem_every),.layers_to_mem(nex_layers_to_mem)) nextLayer (.inVector(layer_sum),.current_spin(current_spin),.clk(clk),.sum(sum));
end
endgenerate

endmodule

//3:2 adder layer
module vector_reduction_layer #(parameter word_size=8, parameter vector_size=3)(
    input [word_size*vector_size-1:0] inVector,
    output [((vector_size/3)*2+(vector_size%3))*(word_size+1)-1:0] outVector
);

genvar i;
generate

    parameter numAdders = vector_size/3;
    parameter numCarries = vector_size%3;

    for(i=0;i<numAdders;i=i+1)begin : reduction_layer
        carry_delay_adder #(.width(word_size))adder(
            .a(inVector[word_size*(i*3+1)-1:word_size*i*3]),
            .b(inVector[word_size*(i*3+2)-1:word_size*(i*3+1)]),
            .c(inVector[word_size*(i*3+3)-1:word_size*(i*3+2)]),

            .sum(outVector[(word_size+1)*(i*2+1)-1:(word_size+1)*i*2]),
            .carry(outVector[(word_size+1)*(i*2+2)-1:(word_size+1)*(i*2+1)])
        );
    end

    for(i=0;i<numCarries;i=i+1)begin : reduction_layer_carry
        assign outVector[(word_size+1)*(i+1+numAdders*2)-1:(word_size+1)*(i+numAdders*2)]
            =   {inVector[word_size*(i+1+numAdders*3)-1],inVector[word_size*(i+1+numAdders*3)-1:word_size*(i+numAdders*3)]};
    end
endgenerate

endmodule

module carry_delay_adder #(parameter width=8)(
    input [width-1:0] a,
    input [width-1:0] b,
    input [width-1:0] c,
    output [width:0] sum,
    output [width:0] carry
);


genvar i;
generate
    for(i=0;i<width;i=i+1)begin : adderGen
        full_adder bitAdder (.a(a[i]),.b(b[i]),.c(c[i]),.sum(sum[i]),.carry(carry[i+1]));
    end
    full_adder last_bit_adder (.a(a[width-1]),.b(b[width-1]),.c(c[width-1]),.sum(sum[width]), .carry());//i dont think this is needed, could just be assigns to the width'th bits
endgenerate
assign carry[0] = 0;


endmodule

module full_adder(input a, input b,input c, output sum, output carry);

assign sum = a ^ b ^ c;
assign carry = ((a^b) & c) | (a & b);

endmodule
