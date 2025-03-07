run:
	$ iverilog -c filelist/list_dummy.f -o simv -g2012 -Wnone
gen_wave:
	$ vvp simv
wave: 
	$ gtkwave waveform/wave.vcd & 
verif:
	$ python3 verification/random_gen_text_cobifive_ori.py -t
clean: 
	$ rm simv 
	$ rm waveform/wave.vcd 
   
