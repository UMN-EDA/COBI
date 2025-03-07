from Cell import Cell
from Event import Event
from Interpolation import linear_interpolation, trilinear_interpolation, interpolate_for_outside_window
import numpy as np
from timing_parse import timing_parse

class Enable(Cell):
    _input_pins  = set(['in_', 'enable'])
    _output_pins = set(['out_'])

    def __init__(self, instance_name, port_map, noise_on=False, three_sig=None):
        super().__init__(instance_name, port_map)
        self.noise_on = noise_on
        self.sigma = self._set_sigma(three_sig)
    
    def _set_sigma(self, three_sig):
        if self.noise_on:
            if three_sig is None:
                raise AttributeError(f"Please specify 3-sigma of noise (in seconds) to be added.")
            else:
                if three_sig <= self._min_delay:
                    raise AttributeError(f"3-sigma number provided is {three_sig}, which is less than min-delay of {self._min_delay} for Enable Cell.")
                elif three_sig >= self._max_delay:
                    raise AttributeError(f"3-sigma number provided is {three_sig}, which is more than max-delay of {self._max_delay} for Enable Cell.")
                sigma = (three_sig/3)
        else:
            sigma = None
        return sigma
    
    def get_output_events(self, e:Event):
        # which input pin is net connected to
        isInput, port = self.find_input_port(e.netname)
        if isInput:
            op_net = self.port2net['out_']
            if port == 'in_':
                op_arr = e.arrival_time + linear_interpolation(e.slew, self._timing_dict['in_input_rise_slew'], self._timing_dict['in_output_fall_delay'])
                op_arr += self.get_noise()
                op_slw = linear_interpolation(e.slew, self._timing_dict['in_input_rise_slew'], self._timing_dict['in_output_fall_slew'])
            elif port == 'enable':
                op_arr = e.arrival_time + linear_interpolation(e.slew, self._timing_dict['enable_input_slew'], self._timing_dict['enable_output_delay'])
                op_slw = linear_interpolation(e.slew, self._timing_dict['enable_input_slew'], self._timing_dict['enable_output_slew'])
            if e.transition == 'r':
                op_tran = 'f'
            else:
                op_tran = 'r'
            return [Event(op_net, op_arr, op_slw, op_tran)]
        else:
            raise ValueError(f"Net '{net}' is not connected to an input of {self.instance_name}.")
    
    def trace_causal_nets(self, netname):
        net_found = False
        output_conn = False
        for p in self.port2net:
            if netname == self.port2net[p]:
                net_found = True
                if p == 'out_':
                    output_conn = True
                    return [self.port2net['enable'], self.port2net['in_']]
        if net_found == False:
            raise ValueError(f"{netname} is not connected to {self.instance_name}")
        if output_conn == False:
            raise ValueError(f"{netname} is not connected to an input of {self.instance_name}")

    def trace_causal_nets_modified(self, netname):
        return self.trace_causal_nets(netname)
    
    def get_noise(self):
        if self.noise_on:
            noise = np.random.normal(0,1)
            return self.sigma*noise
        else:
            return 0
    
def test_enable_cell_timing():
    cell_dict = timing_parse('./data/timing_asap7.txt')
    Enable.set_timing_dict(cell_dict['enable_tile']['timing_dict'])
    xi0 = Enable('xi0',{'in_':'neta', 'enable':'en0', 'out_':'netb'})
    print(xi0.port2net)
    e = Event('en0', 295e-12, 35e-12, 'r')
    #e = Event('neta', 21e-12, 45e-12, 'f')
    o = xi0.get_output_events(e)
    print(o[0])

if __name__ == '__main__':
    test_enable_cell_timing()
