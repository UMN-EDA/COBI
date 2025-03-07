from Cell import Cell
from Event import Event
from Interpolation import linear_interpolation, trilinear_interpolation, interpolate_for_outside_window
import numpy as np
from timing_parse import timing_parse

class Unit(Cell):
    _input_pins  = set([ 'd2u_in', 'l2r_in', 'r2l_in', 'u2d_in'])
    _output_pins = set(['d2u_out','l2r_out','r2l_out','u2d_out'])

    def __init__(self, instance_name, port_map, coupling=0, noise_on=False, three_sig=None):
        super().__init__(instance_name, port_map)
        self.coupling_val = coupling
        self.coupling_suffix = self._get_coupling_suffix(coupling)
        self.noise_on = noise_on
        self.sigma = self._set_sigma(three_sig)
        self.v_backward_val = {}
        self.h_backward_val = {}
        self.h_ev = None
        self.v_ev = None
        self.arrival_diff = None

    def _set_sigma(self, three_sig):
        if self.noise_on:
            if three_sig is None:
                raise AttributeError(f"Please specify 3-sigma of noise (in seconds) to be added.")
            else:
                #if three_sig <= self._min_delay:
                #    raise AttributeError(f"3-sigma number provided is {three_sig}, which is less than min-delay of {self._min_delay} for Unit Cell.")
                #elif three_sig >= self._max_delay:
                #    raise AttributeError(f"3-sigma number provided is {three_sig}, which is more than max-delay of {self._max_delay} for Unit Cell.")
                sigma = (three_sig/3)
        else:
            sigma = None
        return sigma

    def _get_coupling_suffix(self, coupling):
        suffix = "_"
        if coupling > 0:
            suffix += f"p{abs(coupling)}"
        elif coupling < 0:
            suffix += f"m{abs(coupling)}"
        else:
            suffix += f"{abs(coupling)}"
        return suffix

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
        min_slew = None
        max_slew = None
        for key in cls._timing_dict:
            if '_o_slew_' in key:
                if min_slew is None:
                    min_slew = np.min(cls._timing_dict[key])
                else:
                    min_slew = min(min_slew, np.min(cls._timing_dict[key]))
                if max_slew is None:
                    max_slew = np.max(cls._timing_dict[key])
                else:
                    max_slew = max(max_slew, np.max(cls._timing_dict[key]))
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
        cls._min_pd = np.min(cls._timing_dict['pd_arr']) 
        cls._max_pd = np.max(cls._timing_dict['pd_arr']) 
        cls._max_coupling = cls._timing_dict['max_coupling'] 
        if not quiet:
            print(f"F Min delay for {cls.__name__} set to {cls._f_min_delay}.")
            print(f"F Max delay for {cls.__name__} set to {cls._f_max_delay}.")
            print(f"B Min delay for {cls.__name__} set to {cls._b_min_delay}.")
            print(f"B Max delay for {cls.__name__} set to {cls._b_max_delay}.")
            print(f"Min slew for {cls.__name__} set to {min_slew}.")
            print(f"Max slew for {cls.__name__} set to {max_slew}.")
    
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

    def __str__(self):
        return f"Name: {self.instance_name} of type:{self.__class__.__name__}\nPort2Net: {self.port2net} \nCoupling:{self.coupling_val}"

    def get_output_events(self, e1:Event, e2=None):
        if isinstance(e2, Event):
            # process with two events
            return self._get_forward_from_two_events(e1, e2)
        elif isinstance(e2, tuple):
            # process assuming tuple has info of last transition
            return self._get_forward_from_last_tran(e1, e2)
        elif e2 is None:
            # process backward path
            return self._get_backward(e1, True)
    
    def _get_forward_from_two_events(self, e1:Event, e2:Event):
        isInput_1, port_1 = self.find_input_port(e1.netname)
        isInput_2, port_2 = self.find_input_port(e2.netname)
        #print(e1.netname, isInput_1, port_1)
        #print(e2.netname, isInput_2, port_2)
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
                if h.transition == 'r':
                    key_prefix = "hrvf"
                else:
                    key_prefix = "hfvr"
            # do interpolation
            #print(key_prefix)
            #print(h.netname, h.slew, v.netname, v.slew, av_minus_ah, self.coupling_suffix)
            #print(self._timing_dict['tH_arr'])
            #print(self._timing_dict['tV_arr'])
            h_o_del = trilinear_interpolation(h.slew, v.slew, av_minus_ah, \
                                              self._timing_dict[key_prefix+'_h_delay'+self.coupling_suffix], self._timing_dict['tH_arr'],\
                                              self._timing_dict['tV_arr'], self._timing_dict['pd_arr'])
            h_o_slw = trilinear_interpolation(h.slew, v.slew, av_minus_ah, \
                                              self._timing_dict[key_prefix+'_h_o_slew'+self.coupling_suffix], self._timing_dict['tH_arr'],\
                                              self._timing_dict['tV_arr'], self._timing_dict['pd_arr'])
            v_o_del = trilinear_interpolation(h.slew, v.slew, av_minus_ah, \
                                              self._timing_dict[key_prefix+'_v_delay'+self.coupling_suffix], self._timing_dict['tH_arr'],\
                                              self._timing_dict['tV_arr'], self._timing_dict['pd_arr'])
            v_o_slw = trilinear_interpolation(h.slew, v.slew, av_minus_ah, \
                                              self._timing_dict[key_prefix+'_v_o_slew'+self.coupling_suffix], self._timing_dict['tH_arr'],\
                                              self._timing_dict['tV_arr'], self._timing_dict['pd_arr'])
            #print(h_o_del, h_o_slw, v_o_del, v_o_slw)
            h_noise = self.get_noise()
            v_noise = self.get_noise()
            h_o_del += h_noise
            v_o_del += v_noise
            if h_o_del < 0 or v_o_del < 0:
                print(f"H delay + noise = {h_o_delay}, H noise = {h_noise}")
                print(f"V delay + noise = {v_o_delay}, V noise = {v_noise}")
                raise ValueError(f"Delay turned negative. Violates causality.")
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
            if port == 'l2r_in':
                direction = 'h'
            elif port == 'd2u_in':
                direction = 'v'
            else:
                raise ValueError(f"Not a pin on forward path of {self.instance_name}")
            op_port = port.replace('in','out')
            op_net = self.port2net[op_port]
            if e1.transition == e2[1]:
                if e1.transition == 'r':
                    key_prefix = 'hrvr'
                else:
                    key_prefix = 'hfvf'
            else:
                if (e1.transition == 'r' and direction == 'h') or (e1.transition == 'f' and direction == 'v'):
                    key_prefix = 'hrvf'
                else:
                #elif (e1.transition == 'f' and direction == 'h') or (e1.transition == 'r' and direction == 'v'):
                    key_prefix = 'hfvr'
            # find correct delay and slew from matrix
            delay_matrix = self._timing_dict[f'{key_prefix}_{direction}_delay'+self.coupling_suffix]
            slew_matrix = self._timing_dict[f'{key_prefix}_{direction}_o_slew'+self.coupling_suffix]
            if direction == 'h':
                tX_arr = self._timing_dict['tH_arr']
            elif direction == 'v':
                tX_arr = self._timing_dict['tV_arr']
            op_arr = e1.arrival_time + interpolate_for_outside_window(e1.slew, tX_arr, direction, delay_matrix)
            noise = self.get_noise()
            op_arr += noise
            if op_arr < e1.arrival_time:
                print(f"Input arrival: {e1.arrival_time}")
                print(f"Output arrival with noise: {op_arr}, Noise: {noise}, sigma={self.sigma}")
                raise ValueError(f"Causality violated.")
            op_slw = interpolate_for_outside_window(e1.slew, tX_arr, direction, slew_matrix)
            op_tran = e1.invert()
            return [Event(op_net, op_arr, op_slw, op_tran)]
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
    
    def _get_no_coupling_events(self, e1:Event):
        pass

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
        # Find which input causes an event at an output connected to netname
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

    def record(self, e:Event):
        if e.transition == 'r':
            if self.port2net['l2r_in'] == e.netname:
                self.h_ev = e.arrival_time
            elif self.port2net['d2u_in'] == e.netname:
                self.v_ev = e.arrival_time
            if self.h_ev is not None and self.v_ev is not None:
                self.arrival_diff = abs(self.h_ev - self.v_ev)
        return

    def get_noise(self):
        if self.noise_on:
            noise = np.random.normal(0,1)
            return self.sigma*noise
        else:
            return 0    

def test_unit_cell_timing():
    cell_dict = timing_parse('./DDUDU_timing_max7_POSTLAYOUT.txt')
    #cell_dict = timing_parse('./timing_ddudu.txt')
    #cell_dict = timing_parse('./timing_max7.txt')
    #cell_dict = timing_parse('/scratch/kumar663/GF12/sim/android/separate_char/timing.txt')
    Unit.set_timing_dict(cell_dict['unit_coupling_tile']['timing_dict'])
    port_map = {'l2r_in':'net13', 'l2r_out':'net14', 'r2l_in':'net14', 'r2l_out':'net16',\
                'd2u_in':'net19', 'd2u_out':'net10', 'u2d_in':'net11', 'u2d_out':'net20'}
    #for coupling in range(-1*Unit._max_coupling, Unit._max_coupling+1):
    #    xis = Unit('xi0', port_map, coupling)
    #    print(f"{xis.instance_name}")
    #    print(f"{xis.port2net}")
    #    print(f"{xis.coupling_val}")
    #    print("Checking two event timing.")
    #    pd_arr = np.linspace(Unit._min_pd, Unit._max_pd, 11, endpoint=True)
    #    for av_minus_ah in pd_arr:
    #        e1 = Event('net13', 200e-12, 45e-12, 'r')
    #        e2 = Event('net19', 200e-12 + av_minus_ah, 45e-12, 'r')
    #        #for cnt in range(100):
    #        o = xis.get_output_events(e1, e2)
    #        pstr = f"{e1} {e2} caused \n  "
    #        for e in o:
    #            pstr += f"{e} "
    #        print(pstr)
    #    print("Checking one event forward timing.")
    #    for htran in ['r', 'f']:
    #        for vtran in ['r', 'f']:
    #            t1 = ('net19', vtran)
    #            e1 = Event('net13', 100e-12, 45e-12, htran)
    #            o = xis.get_output_events(e1, t1)
    #            print(f"{e1} caused {o[0]} with last tran {t1}.")
    #            t2 = ('net13', htran)
    #            e2 = Event('net19', 100e-12, 45e-12, vtran)
    #            o = xis.get_output_events(e2, t2)
    #            print(f"{e2} caused {o[0]} with last tran {t2}.")
    #    print("Checking one event backward timing.")
    #    e1 = Event('net14', 100e-12, 55e-12, 'f')
    #    o = xis.get_output_events(e1)
    #    print(f"{o[0]}")
    xis = Unit('xi0', port_map, 0)
    print(f"Random test:")
    e1 = Event('net19', 411.80e-12, 18.93e-12, 'r')
    #e2 = Event('net13', 1502452.21e-12, 34.22e-12, 'f')
    #o = xis.get_output_events(e1, e2)
    o = xis.get_output_events(e1, ('net13', 'f'))
    for e in o:
        print(e)

if __name__ == '__main__':
    test_unit_cell_timing()
