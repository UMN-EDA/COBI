from Cell import Cell
from Event import Event
from Interpolation import linear_interpolation, trilinear_interpolation, interpolate_for_outside_window
from timing_parse import timing_parse
import numpy as np

class Short(Cell):
    _input_pins  = set([ 'd2u_in', 'l2r_in', 'r2l_in', 'u2d_in'])
    _output_pins = set(['d2u_out','l2r_out','r2l_out','u2d_out'])

    def __init__(self, instance_name, port_map):
        super().__init__(instance_name, port_map)
        self.coupling_val = 1
        self.v_backward_val = {}
        self.h_backward_val = {}

    @classmethod
    def set_timing_dict(cls, timing_dict, quiet=False):
        cls._timing_dict = timing_dict
        l = cls._timing_dict['pd_arr'][0]
        r = cls._timing_dict['pd_arr'][-1]
        cls._window = max(abs(l), abs(r))
        if not quiet:
            print(f"Window for {cls.__name__} set to {cls._window}")
        f_min_delay = None
        f_max_delay = None
        r_min_delay = None
        r_max_delay = None
        for key in cls._timing_dict:
            if 'delay' in key and key not in ['output_rise_delay', 'output_fall_delay']:
                if f_min_delay is None:
                    f_min_delay = np.min(cls._timing_dict[key])
                else:
                    f_min_delay = min(f_min_delay, np.min(cls._timing_dict[key]))
                if f_max_delay is None:
                    f_max_delay = np.max(cls._timing_dict[key])
                else:
                    f_max_delay = max(f_max_delay, np.max(cls._timing_dict[key]))
        b_min_delay =  min(np.min(cls._timing_dict['output_rise_delay']), np.min(cls._timing_dict['output_fall_delay']))
        b_max_delay =  max(np.max(cls._timing_dict['output_rise_delay']), np.max(cls._timing_dict['output_fall_delay']))
        cls._f_min_delay = f_min_delay
        cls._f_max_delay = f_max_delay
        cls._b_min_delay = b_min_delay
        cls._b_max_delay = b_max_delay
        if not quiet:
            print(f"F Min delay for {cls.__name__} set to {cls._f_min_delay}.")
            print(f"F Max delay for {cls.__name__} set to {cls._f_max_delay}.")
            print(f"B Min delay for {cls.__name__} set to {cls._b_min_delay}.")
            print(f"B Max delay for {cls.__name__} set to {cls._b_max_delay}.")

    def get_min_delay(self, direction:str):
        # 'F' for forward path, 'B' for return/back path
        if direction == 'F':
            return self._f_min_delay
        else:
            return self._b_min_delay

    def get_max_delay(self, direction:str):
        if direction == 'F':
            return self._f_max_delay
        else:
            return self._b_max_delay

    def get_output_events(self, e1:Event, e2=None):
        if isinstance(e2, Event):
            # process with two events
            return self._get_forward_from_two_events(e1, e2)
        elif isinstance(e2, tuple):
            # process assuming tuple has info of last transition
            raise ValueError(f"The Short Cell {self.instance_name} received only one event. The other event was not found.")
        elif e2 is None:
            # process backward path
            return self._get_backward(e1, True)
    
    def _get_forward_from_two_events(self, e1:Event, e2:Event):
        isInput_1, port_1 = self.find_input_port(e1.netname)
        isInput_2, port_2 = self.find_input_port(e2.netname)
        if isInput_1 and isInput_2:
            # do here
            if port_1 == 'l2r_in' and port_2 == 'd2u_in':
                h = e1
                v = e2
            elif port_1 == 'd2u_in' and port_2 == 'l2r_in':
                h = e2
                v = e1
            else:
                raise ValueError(f"Incorrect pair of pins for {self.instance_name}.")
            av_minus_ah = v.arrival_time - h.arrival_time
            key_prefix = ""
            if h.transition == v.transition:
                if h.transition == 'r':
                    key_prefix = "hrvr"
                else:
                    key_prefix = "hfvf"
                # choose a numpy array
            else:
                # choose another numpy array
                # unlikely to occur for Short cell if vertical and horizontal ROs were enabled together
                if h.transition == 'r':
                    key_prefix = "hrvf"
                else:
                    key_prefix = "hfvr"
                raise ValueError(f"Check why Short cell {self.instance_name} received two edges of different kind.")
            # do interpolation
            h_o_del = trilinear_interpolation(h.slew, v.slew, av_minus_ah, \
                                              self._timing_dict[key_prefix+'_h_delay'], self._timing_dict['tH_arr'],\
                                              self._timing_dict['tV_arr'], self._timing_dict['pd_arr'])
            h_o_slw = trilinear_interpolation(h.slew, v.slew, av_minus_ah, \
                                              self._timing_dict[key_prefix+'_h_o_slew'], self._timing_dict['tH_arr'],\
                                              self._timing_dict['tV_arr'], self._timing_dict['pd_arr'])
            v_o_del = trilinear_interpolation(h.slew, v.slew, av_minus_ah, \
                                              self._timing_dict[key_prefix+'_v_delay'], self._timing_dict['tH_arr'],\
                                              self._timing_dict['tV_arr'], self._timing_dict['pd_arr'])
            v_o_slw = trilinear_interpolation(h.slew, v.slew, av_minus_ah, \
                                              self._timing_dict[key_prefix+'_v_o_slew'], self._timing_dict['tH_arr'],\
                                              self._timing_dict['tV_arr'], self._timing_dict['pd_arr'])
            #populate events
            h_e = Event(self.port2net['l2r_out'], h.arrival_time + h_o_del, h_o_slw, h.invert())
            v_e = Event(self.port2net['d2u_out'], v.arrival_time + v_o_del, v_o_slw, v.invert())
            return [h_e, v_e]
        else:
            raise ValueError(f"Not connected to input of {self.instance_name}.")

    def _get_forward_from_last_tran(self, e1:Event, e2:tuple):
        # e2 is a 2-tuple with first element being netname, second being last transition type ('r'/'f')
        isInput, port = self.find_input_port(e1.netname)
        if isInput:
            if port in ['l2r_in', 'd2u_in']:
                op_port = port.replace('in','out')
                op_net = self.port2net[op_port]
            else:
                raise ValueError(f"Not a pin on forward path of {self.instance_name}")
            if e1.transition == e2[1]:
                op_arr = e1.arrival_time + same_slew_delay_outside_window
                op_slw = same_slew_outside_window
            else:
                op_arr = e1.arrival_time + opp_slew_delay_outside_window
                op_slw = opp_slew_outside_window
            return [Event(op_net, op_arr, op_slw, e1.invert())]
        else:
            raise ValueError(f"Not connected to input of {self.instance_name}.")
    
    def _get_backward(self, e1:Event, reuse=False):
        isInput, port = self.find_input_port(e1.netname)
        if isInput:
            if port in ['r2l_in','u2d_in']:
                op_port = port.replace('in','out')
                op_net  = self.port2net[op_port]
                op_tran = e1.invert()
                if (len(self.v_backward_val) < 2) or (len(self.h_backward_val) < 2) or reuse == False:
                    if e1.transition == 'r':
                        op_delay= linear_interpolation(e1.slew, self._timing_dict['input_rise_slew'], self._timing_dict['output_rise_delay'])
                        op_arr  = e1.arrival_time + op_delay
                        op_slw  = linear_interpolation(e1.slew, self._timing_dict['input_rise_slew'], self._timing_dict['output_rise_slew'])
                    else:
                        op_delay= linear_interpolation(e1.slew, self._timing_dict['input_fall_slew'], self._timing_dict['output_fall_delay'])
                        op_arr  = e1.arrival_time + op_delay
                        op_slw  = linear_interpolation(e1.slew, self._timing_dict['input_fall_slew'], self._timing_dict['output_fall_slew'])
                    if port == 'r2l_in':
                        self.h_backward_val[e1.transition] = (op_delay, op_slw)
                    else:
                        self.v_backward_val[e1.transition] = (op_delay, op_slw)
                else:
                    if port == 'r2l_in':
                        op_arr = e1.arrival_time + self.h_backward_val[e1.transition][0]
                        op_slw = self.h_backward_val[e1.transition][1]
                    else:
                        op_arr = e1.arrival_time + self.v_backward_val[e1.transition][0]
                        op_slw = self.v_backward_val[e1.transition][1]
                return [Event(op_net, op_arr, op_slw, op_tran)]
            else:
                raise ValueError(f"Not connected to backward input of {self.instance_name}.")
        else:
            raise ValueError(f"Not connected to input of {self.instance_name}.")

    def trace_causal_nets(self, netname):
        net_found = False
        port = None
        for p in self.port2net:
            if netname == self.port2net[p]:
                net_found = True
                if p in self._output_pins:
                    port = p
        if net_found == False:
            raise ValueError(f"{netname} is not connected to {self.instance_name}")
        if port is None:
            raise ValueError(f"{netname} is not connected to output of {self.instance_name}")
        if port == 'd2u_out' or port == 'l2r_out':
            return [self.port2net['d2u_in'], self.port2net['l2r_in']]
        elif port == 'u2d_out':
            return [self.port2net['u2d_in']]
        elif port == 'r2l_out':
            return [self.port2net['r2l_in']]    

    def trace_causal_nets_modified(self, netname):
        #net_found = False
        #for p in self.port2net:
        #    if netname == self.port2net[p]:
        #        net_found = True
        #        if p in self._output_pins:
        #            port = p
        #if net_found == False:
        #    raise ValueError(f"{netname} is not connected to {self.instance_name}")
        #if port is None:
        #    raise ValueError(f"{netname} is not connected to output of {self.instance_name}")
        if netname in self.net2ports:
            port = None
            for p in self.net2ports[netname]:
                if p in self._output_pins:
                    port = p
            if port is None:
                raise ValueError(f"{netname} is not connected to output of {self.instance_name}")
        else:
            raise ValueError(f"{netname} is not connected to {self.instance_name}")
        op_port = port.replace('out', 'in')
        return [self.port2net[op_port]] 

    def get_assoc_net(self, netname, logfile=None, log=False):
        net_found = False
        for p in self.port2net:
            if netname == self.port2net[p]:
                if logfile is not None and log == True:
                    logfile.write(f"{netname} is connected to {p}.\n")
                port = p
                if port == 'd2u_in':
                    return self.port2net['l2r_in']
                elif port == 'l2r_in':
                    return self.port2net['d2u_in']
                else:
                    return None
        if net_found == False:
            raise ValueError(f"{netname} is not connected to {self.instance_name}")
    
    def get_window(self):
        return self._window

def test_short_cell_timing():
    cell_dict = timing_parse('./data/timing_asap7.txt')
    Short.set_timing_dict(cell_dict['short_tile']['timing_dict'])
    port_map = {'l2r_in':'net12', 'l2r_out':'net13', 'r2l_in':'net16', 'r2l_out':'net15',\
                'd2u_in':'net17', 'd2u_out':'net8' , 'u2d_in':'net9' , 'u2d_out':'net18'}
    xis = Short('xi0', port_map)
    print(xis.instance_name)
    print(xis.port2net)
    #print("Checking two event timing.")
    #for av_minus_ah in range(-100, 100, 10):
    #    e1 = Event('net12', 200e-12, 45e-12, 'r')
    #    e2 = Event('net17', 200e-12 + (av_minus_ah*1e-12), 45e-12, 'r')
    #    o = xis.get_output_events(e1, e2)
    #    pstr = f"{e1} {e2} caused \n  "
    #    for e in o:
    #        pstr += f"{e} "
    #    print(pstr)
    #print("Checking one event forward timing.")
    #for tran in ['r', 'f']:
    #    # Only checking for rr and ff transitions
    #    e1 = Event('net12', 100e-12, 45e-12, tran)
    #    o = xis.get_output_events(e1, ('net17', tran))
    #    print(f"{e1} caused {o[0]}")
    #print("Checking one event backward timing.")
    #e1 = Event('net16', 100e-12, 55e-12, 'f')
    #o = xis.get_output_events(e1)
    #print(f"{o[0]}")
    e1 = Event('net12', 343.69e-12, 14.75e-12, 'f')
    e2 = Event('net17', 343.69e-12, 14.75e-12, 'f')
    o = xis.get_output_events(e1, e2)
    print(o[0], o[1])

if __name__ == '__main__':
    test_short_cell_timing()
