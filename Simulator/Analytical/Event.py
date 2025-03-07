class Event():
	_precision = 1e-12
	def __init__(self, netname:str, arrival_time:float, slew:float, transition:str):
		self.netname = netname
		self.arrival_time = arrival_time
		self.slew = slew
		self.transition = transition
	
	def __str__(self):
		return f"Net: {self.netname}, Arrival: {self.arrival_time/self._precision:.2f}ps, Slew: {self.slew/self._precision:.2f}ps, Tran: {self.transition}"

	def __lt__(self, other):
		return self.arrival_time < other.arrival_time
	
	def invert(self):
		if self.transition == 'r':
			return 'f'
		else:
			return 'r'

