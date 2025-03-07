module vector_splitter_spin (
    input [`NUM_ROW-1:0] in_vector,
    input step,
    output [`NUM_ROW/2 - 1:0] out_vector
);

assign out_vector = step ? (in_vector[`NUM_ROW-1:`NUM_ROW/2]):(in_vector[`NUM_ROW/2-1:0]);

endmodule
