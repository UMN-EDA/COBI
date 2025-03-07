import numpy as np

class Cell():
	_input_pins  = set()
	_output_pins = set()
	_timing_dict = None
	
	@classmethod
	def set_timing_dict(cls, timing_dict, quiet=False):
		cls._timing_dict = timing_dict
		min_delay = None
		max_delay = None
		for key in cls._timing_dict:
			if 'delay' in key:
				if min_delay is None:
					min_delay = np.min(cls._timing_dict[key])
				else:
					min_delay = min(min_delay, np.min(cls._timing_dict[key]))
				if max_delay is None:
					max_delay = np.max(cls._timing_dict[key])
				else:
					max_delay = max(max_delay, np.max(cls._timing_dict[key]))
		cls._min_delay = min_delay
		cls._max_delay = max_delay
		if not quiet:
			print(f"Min delay for {cls.__name__} set to {cls._min_delay}.")
			print(f"Max delay for {cls.__name__} set to {cls._max_delay}.")

	@classmethod
	def show_timing_dict(cls):
		if cls._timing_dict is None:
			print(f"Timing dict for {cls.__name__} not set yet.")
			return 
		for field in cls._timing_dict:
			pstr = f"{field} , {type(cls._timing_dict[field])}"
			if isinstance(cls._timing_dict[field], np.ndarray):
				pstr += f", Shape = {cls._timing_dict[field].shape}"
			elif isinstance(cls._timing_dict[field], list):
				pstr += f", len = {len(cls._timing_dict[field])}"
			print(pstr)

	def __init__(self, instance_name, port_map):
		self.instance_name = instance_name
		self.port2net = self._set_port2net(port_map)
		self.net2ports= self._set_net2ports()
	
	def __new__(cls, *args, **kwargs):
		# Prevent instantiation of Cell objects
		if cls is Cell:
			raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
		return super().__new__(cls)

	def __str__(self):
		return f"Name: {self.instance_name} of type:{self.__class__.__name__}\nPort2Net: {self.port2net}"
	
	def _set_port2net(self, port_map):
		for ip in self._input_pins:
			if ip not in port_map:
				raise ValueError(f"No mapping to net for input port '{ip}'.")
		for op in self._output_pins:
			if op not in port_map:
				raise ValueError(f"No mapping to net for output port '{op}'.")
		for pin in port_map:
			if (pin not in self._input_pins) and (pin not in self._output_pins):
				raise ValueError(f"No pin called '{pin}'.")
		return port_map

	def _set_net2ports(self):
		net2ports = {}
		for p in self.port2net:
			net = self.port2net[p]
			if net not in net2ports:
				net2ports[net] = []
			net2ports[net].append(p)
		return net2ports

	def get_inputs(self):
		return self._input_pins
	
	def get_outputs(self):
		return self._output_pins

	def is_input(self, netname):
		#net_found = False
		#for port in self.port2net:
		#	if netname == self.port2net[port]:
		#		net_found = True
		#		if port in self._input_pins:
		#			return True
		#if net_found == False:
		#	raise ValueError(f"Net {netname} is not connected to {self.instance_name}")
		#return False
		if netname in self.net2ports:
			for p in self.net2ports[netname]:
				if p in self._input_pins:
					# Safe to return once any input port is found
					return True
			# All pins checked and none were inputs, return False
			return False
		else:
			raise ValueError(f"Net {netname} is not connected to {self.instance_name}")

	def is_output(self, netname):
		#net_found = False
		#for port in self.port2net:
		#	if netname == self.port2net[port]:
		#		net_found = True
		#		if port in self._output_pins:
		#			return True
		#if net_found == False:
		#	raise ValueError(f"Net {netname} is not connected to {self.instance_name}")
		#return False
		if netname in self.net2ports:
			for p in self.net2ports[netname]:
				if p in self._output_pins:
					# Safe to return once any output port is found
					return True
			# All pins checked and none were outputs, return False
			return False
		else:
			raise ValueError(f"Net {netname} is not connected to {self.instance_name}")
	
	def find_input_port(self, net):
		#net_found = False
		#for p in self.port2net:
		#	if self.port2net[p] == net:
		#		if p in self._input_pins:
		#			net_found = True
		#			return net_found, p
		#return net_found, None
		if net in self.net2ports:
			for p in self.net2ports[net]:
				if p in self._input_pins:
					return True, p
			# All pins checked and none were inputs, return False
			return False, None
		else:
			raise ValueError(f"Net {netname} is not connected to {self.instance_name}")
	
	def get_min_delay(self, direction='B'):
        # direction = 'F' or 'B'
		return self._min_delay
	
	def get_max_delay(self, direction='B'):
        # direction = 'F' or 'B'
		return self._max_delay
