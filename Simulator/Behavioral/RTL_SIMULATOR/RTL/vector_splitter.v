module vector_splitter #(parameter word_size = 1, parameter in_size = 46) (
    input [`WORD_WIDTH*(`ARRAY_SIZE-4)-1:0] in_vector,
    input step,
    output [`WORD_WIDTH*(`ARRAY_SIZE-4)/2-1:0] out_vector
);

assign out_vector = step ? (in_vector[`WORD_WIDTH*(`ARRAY_SIZE-4)-1:`WORD_WIDTH*(`ARRAY_SIZE-4)/2]):(in_vector[`WORD_WIDTH*(`ARRAY_SIZE-4)/2-1:0]);

endmodule
