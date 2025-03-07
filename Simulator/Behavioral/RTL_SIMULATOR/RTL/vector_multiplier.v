// Tag.01 yhhong 2023.04.08 Change weight format [1:0], [1] : magnitude, [0] : sign (positive :1, negative :0)

//converts input value to twos complement, sets sign based on spins
module vector_multiplier #(parameter word_size=4, parameter array_size=51)(
    input [word_size*(array_size-5)/2-1:0] weight_vector,
    input [(array_size-5)/2-1:0] spin_vector,
    output [(array_size-5)*word_size/2-1:0] product_vector
);

    genvar i;
    generate
        for(i=0;i<(array_size-5)/2;i=i+1)begin
        spinMultiplier #(.word_size(word_size)) multiplier (
            .sign_magnitude(weight_vector[word_size*(i+1)-1-:word_size]),
            .spin_j(spin_vector[i]),
            .signed_out(product_vector[word_size*(i+1)-1-:word_size])
            );
        end
    endgenerate
endmodule

module spinMultiplier #(parameter word_size=4)(
    input [word_size-1:0] sign_magnitude,
    input spin_j,
    output [word_size-1:0] signed_out
);

generate
if(word_size==2)begin
//assign signed_out[0] = (sign_magnitude[0]);   // Tag.01 yhhong
assign signed_out[0] = (sign_magnitude[1]);   
//assign signed_out[1] = (sign_magnitude[0])?~( spin_j ^ sign_magnitude[1]):0;  // Tag.01 yhhong
assign signed_out[1] = (sign_magnitude[1])? ~( spin_j ^ (~sign_magnitude[0])):0;   
end
else begin
    wire sign;
    wire weight_sign;

    //assign weight_sign = sign_magnitude[word_size-1];
    assign weight_sign = ~sign_magnitude[0];
    assign sign = (weight_sign  ^ spin_j);

    wire [word_size-2:0] invertedInput;
    wire [word_size-1:0] negativeValue;
    wire [word_size-1:0] positiveValue;

    wordInverter #(.word_size(word_size-1)) inputInverter(.in(sign_magnitude[word_size-1:1]),.out(invertedInput));
    assign negativeValue = ({1'b1,invertedInput} + 1'b1);
    assign positiveValue = {1'b0,sign_magnitude[word_size-1:1]};

    assign signed_out = (sign)?positiveValue:negativeValue;
end
endgenerate
endmodule

module wordInverter #(parameter word_size=4)(
    input [word_size-1:0] in,
    output [word_size-1:0] out
);
genvar i;
generate
    for(i=0;i<word_size;i=i+1)begin
        assign out[i] = ~in[i];
    end
endgenerate
endmodule
