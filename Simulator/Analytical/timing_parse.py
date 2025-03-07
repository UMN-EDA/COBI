# function to parse the timing file
import re
import argparse
import numpy as np

def get_enable_timing(fileobj):
    #for line in fileobj:
    t_dict = {}
    for i in range(9):
        line = fileobj.readline()
        line_arr = line.split()
        meas_name = line_arr[0][:-1]
        t_arr = []
        line = fileobj.readline()
        line_arr = line.split()
        for elm in line_arr:
            t_arr.append(float(elm))
        t_dict[meas_name] = t_arr
    return t_dict

def get_short_timing(fileobj):
    t_dict = {}
    tH_arr = []
    line = fileobj.readline()
    line = fileobj.readline()
    line_arr = line.split()
    for val in line_arr:
        tH_arr.append(float(val))
    t_dict['tH_arr'] = tH_arr
    tV_arr = []
    line = fileobj.readline()
    line = fileobj.readline()
    line_arr = line.split()
    for val in line_arr:
        tV_arr.append(float(val))
    t_dict['tV_arr'] = tV_arr
    pd_arr = []
    line = fileobj.readline()
    line = fileobj.readline()
    line_arr = line.split()
    for val in line_arr:
        pd_arr.append(float(val))
    t_dict['pd_arr'] = pd_arr
    for c in range(8): #8 measures
        line = fileobj.readline()
        line = line.strip()
        meas_name = line[:-1]
        np_arr = np.zeros((len(tH_arr), len(tV_arr), len(pd_arr)))
        for i in range(len(pd_arr)):
            line = fileobj.readline()
            for j in range(len(tH_arr)):
                line = fileobj.readline()
                line_arr = line.split()
                for k, val in enumerate(line_arr):
                    np_arr[j, k, i] = float(val)
        line = fileobj.readline()
        t_dict[meas_name] = np_arr
    for i in range(6):
        line = fileobj.readline()
        line_arr = line.split()
        meas_name = line_arr[0][:-1]
        t_arr = []
        line = fileobj.readline()
        line_arr = line.split()
        for elm in line_arr:
            t_arr.append(float(elm))
        t_dict[meas_name] = t_arr
    return t_dict

def get_unit_timing(fileobj):
    t_dict = {}
    line = fileobj.readline()
    line_arr = line.split()
    max_coupling = int(line_arr[-1]) # Number of coupling levels
    c_vals = 2*max_coupling + 1
    t_dict['max_coupling'] = max_coupling
    tH_arr = []
    line = fileobj.readline()
    line = fileobj.readline()
    line_arr = line.split()
    for val in line_arr:
        tH_arr.append(float(val))
    t_dict['tH_arr'] = tH_arr
    tV_arr = []
    line = fileobj.readline()
    line = fileobj.readline()
    line_arr = line.split()
    for val in line_arr:
        tV_arr.append(float(val))
    t_dict['tV_arr'] = tV_arr
    pd_arr = []
    line = fileobj.readline()
    line = fileobj.readline()
    line_arr = line.split()
    for val in line_arr:
        pd_arr.append(float(val))
    t_dict['pd_arr'] = pd_arr
    for c in range(16*c_vals): # 16 measures for each coupling value
        line = fileobj.readline()
        line = line.strip()
        meas_name = line[:-1]
        np_arr = np.zeros((len(tH_arr), len(tV_arr), len(pd_arr)))
        for i in range(len(pd_arr)):
            line = fileobj.readline()
            for j in range(len(tH_arr)):
                line = fileobj.readline()
                line_arr = line.split()
                for k, val in enumerate(line_arr):
                    np_arr[j, k, i] = float(val)
        line = fileobj.readline()
        t_dict[meas_name] = np_arr
    for i in range(6):
        line = fileobj.readline()
        line_arr = line.split()
        meas_name = line_arr[0][:-1]
        t_arr = []
        line = fileobj.readline()
        line_arr = line.split()
        for elm in line_arr:
            t_arr.append(float(elm))
        t_dict[meas_name] = t_arr
    return t_dict

def get_cell(cell_name, fileobj):
    # Get inputs
    line = fileobj.readline()
    line_arr = line.split()
    inputs = line_arr[1:]
    # Get outputs
    line = fileobj.readline()
    line_arr = line.split()
    outputs = line_arr[1:]
    # Get nom delay
    line = fileobj.readline()
    line_arr = line.split()
    nominal_delay = int(line_arr[-1]) 
    # Get nom op tran
    line = fileobj.readline()
    line_arr = line.split()
    nominal_op_tran = int(line_arr[-1]) 
    # Get unateness
    line = fileobj.readline()
    line_arr = line.split()
    unateness = line_arr[-1]
    # Get trigger groups
    line = fileobj.readline()
    grps_re = re.compile(r'\[\w+[,\s\w+]+\]')
    ports_re = re.compile(r'\w+')
    groups = grps_re.findall(line)
    if groups:
        trig_grp = set()
        for grp in groups:
            ports = ports_re.findall(grp)
            tgrp = set()
            for port in ports:
                tgrp.add(port)
            trig_grp.add(frozenset(tgrp))
    else:
        raise SyntaxError(f"Please assign trigger groups for all cells.")
    # Get target groups
    line = fileobj.readline()
    targ_grps_re = re.compile(r'\[\w+:\w+\]')
    targ_ports_re = re.compile(r'\w+')
    targ_grps_list = targ_grps_re.findall(line)
    if targ_grps_list:
        targ_grp = {}
        for grp in targ_grps_list:
            ports = targ_ports_re.findall(grp)
            if ports:
                ip = ports[0]
                op = ports[1]
                targ_grp[ip] = op
            else:
                raise SyntaxError(f"Please assign input output pairs for all target groups.")
    else:
        raise SyntaxError(f"Please assign target groups for all cells.")
    t_dict = None    
    if cell_name == 'enable_tile':
        t_dict = get_enable_timing(fileobj)
    elif cell_name == 'short_tile':
        t_dict = get_short_timing(fileobj)
    elif cell_name == 'unit_coupling_tile':
        t_dict = get_unit_timing(fileobj)

    return inputs, outputs, nominal_delay, nominal_op_tran, unateness, trig_grp, targ_grp, t_dict

def trilinear_interpolate(tH, tV, pd, matrix, tH_arr, tV_arr, phase_diff_arr):
    if tH < tH_arr[0] or tH > tH_arr[-1]: # assumes tH_arr is sorted in inc order
        raise ValueError(f"First coordinate out of array.")
    if tV < tV_arr[0] or tV > tV_arr[-1]: # assumes tv_arr is sorted in inc order
        raise ValueError(f"Second coordinate out of array.")

    # if the assumption that arrays are sorted is always valid,
    # change the code below to do a binary search instead of linear
    # right now the arrays are small so the difference doesnt matter,
    # for for larger arrays and multiple calls, this might accumulate
    # In the words of Kevin, many small time make big time
    for hidx in range(0, len(tH_arr)-1):
        if tH >= tH_arr[hidx] and tH <= tH_arr[hidx+1]:
            hidx_lt = hidx
            break
    for vidx in range(0, len(tV_arr)-1):
        if tV >= tV_arr[vidx] and tV <= tV_arr[vidx+1]:
            vidx_lt = vidx
            break
    # Instead of interpolating when phase_diff is outside bounds,
    # Try clamping to the values at terminal phase_differences
    if pd < phase_diff_arr[0]:
        pdidx_lt = 0 
    elif pd > phase_diff_arr[-1]:
        pdidx_lt = len(phase_diff_arr)-2 
    else:
        for pdidx in range(0, len(phase_diff_arr)-1):
            if pd >= phase_diff_arr[pdidx] and pd <= phase_diff_arr[pdidx+1]:
                pdidx_lt = pdidx
                break
    tH_d = (tH - tH_arr[hidx_lt])/(tH_arr[hidx_lt+1] - tH_arr[hidx_lt])
    tV_d = (tV - tV_arr[vidx_lt])/(tV_arr[vidx_lt+1] - tV_arr[vidx_lt])
    pd_d = (pd - phase_diff_arr[pdidx_lt])/(phase_diff_arr[pdidx_lt+1] - phase_diff_arr[pdidx_lt])

    c000 = matrix[hidx_lt  , vidx_lt  , pdidx_lt  ]
    c100 = matrix[hidx_lt+1, vidx_lt  , pdidx_lt  ]
    c010 = matrix[hidx_lt  , vidx_lt+1, pdidx_lt  ]
    c110 = matrix[hidx_lt+1, vidx_lt+1, pdidx_lt  ]
    c001 = matrix[hidx_lt  , vidx_lt  , pdidx_lt+1]
    c101 = matrix[hidx_lt+1, vidx_lt  , pdidx_lt+1]
    c011 = matrix[hidx_lt  , vidx_lt+1, pdidx_lt+1]
    c111 = matrix[hidx_lt+1, vidx_lt+1, pdidx_lt+1]

    cx00 = c000*(1-tH_d) + c100*tH_d
    cx01 = c001*(1-tH_d) + c101*tH_d
    cx10 = c010*(1-tH_d) + c110*tH_d
    cx11 = c011*(1-tH_d) + c111*tH_d
    cxx0 = cx00*(1-tV_d) + cx10*tV_d
    cxx1 = cx01*(1-tV_d) + cx11*tV_d
    c    = cxx0*(1-pd_d) + cxx1*pd_d

    #print(f"{tH_arr[hidx_lt]} {tH_arr[hidx_lt+1]}")
    #print(f"{tV_arr[vidx_lt]} {tV_arr[vidx_lt+1]}")
    #print(f"{phase_diff_arr[pdidx_lt]} {phase_diff_arr[pdidx_lt+1]}")
    #print(f"c000 = {c000} c100 = {c100} c010 = {c010} c110 = {c110}")
    #print(f"c001 = {c001} c101 = {c101} c011 = {c011} c111 = {c111}")
    return c

def linear_interpolation(x, input_arr, output_arr):
    # use binary search if the input array can be large
    # consider similar change in trilinear interp function as well
    if len(input_arr) != len(output_arr):
        raise ValueError(f"Length of arrays should be equal for interpolation.")
    if x < input_arr[0] or x > input_arr[-1]:
        raise ValueError(f"Input outside array bounds for linear interpolation.")
    for i in range(len(input_arr)-1):
        if x >= input_arr[i] and x <= input_arr[i+1]:
            l_idx = i
            break
    x_d = (x - input_arr[l_idx])/(input_arr[l_idx+1] - input_arr[l_idx]) 
    y = output_arr[l_idx]*(1-x_d) + output_arr[l_idx+1]*x_d
    return y

def get_forward_enable(activity_dict, cell_type, cell_dict):
    if len(activity_dict)!=1:
        raise ValueError(f"Only one pin expected for enable cell.")
    for in_pin in activity_dict:
        arrival_time, slew, transition, netname = activity_dict[in_pin]
    info_dict = cell_dict['enable_tile']
    timing_dict = info_dict['timing_dict']
    # negative unateness of enable cell
    if transition == 'r':
        iptran = 'rise'
        optran = 'fall'
    elif transition == 'f':
        iptran = 'fall'
        optran = 'rise'
    else:
        raise ValueError(f"Transition in activity tuple is invalid.")
    if in_pin == 'in_':
        op_delay = linear_interpolation(slew, timing_dict[f'in_input_{iptran}_slew'], timing_dict[f'in_output_{optran}_delay'])
        op_slew  = linear_interpolation(slew, timing_dict[f'in_input_{iptran}_slew'], timing_dict[f'in_output_{optran}_slew'])
    elif in_pin == 'enable':
        op_delay = linear_interpolation(slew, timing_dict['enable_input_slew'], timing_dict['enable_output_delay'])
        op_slew  = linear_interpolation(slew, timing_dict['enable_input_slew'], timing_dict['enable_output_slew'])
    else:
        raise ValueError(f"Pin name is wrong for enable tile.")
    return {'out_':(op_delay, op_slew, optran[0])}

def get_forward_sh_uc(activity_dict, cell_type, cell_dict, coupling=0):
    suffix = ""
    if cell_type == 'unit_coupling_tile':
        suffix += "_"
        if coupling > 0:
            suffix += f"p{abs(coupling)}"
        elif coupling < 0:
            suffix += f"m{abs(coupling)}"
        else:
            suffix += f"{abs(coupling)}"
    # {'l2r_in':(arr,slew,tran), 'd2u_in':(arr,slew,tran)}
    info_dict = cell_dict[cell_type]
    timing_dict = info_dict['timing_dict']
    # Pins in activty dict should be in th same trigger group
    trigger_grp = {pinname for pinname in activity_dict}
    if trigger_grp not in info_dict['trigger_groups']:
        raise ValueError(f"Invalid trigger group.")
    meas_pre = "" 
    if 'l2r_in' in activity_dict:
        meas_pre += f"h{activity_dict['l2r_in'][2]}"
        h_key = 'l2r_in'
        h_tuple = activity_dict['l2r_in']
        h_pin = 'l2r_out'
    elif 'r2l_in' in activity_dict:
        meas_pre += f"h{activity_dict['r2l_in'][2]}"
        h_key = 'r2l_in'
        h_tuple = activity_dict['r2l_in']
        h_pin = 'r2l_out'
    else:
        raise ValueError(f"Not a valid horizontal input of short tile.")
    if 'd2u_in' in activity_dict:
        meas_pre += f"v{activity_dict['d2u_in'][2]}"
        v_key = 'd2u_in'
        v_tuple = activity_dict['d2u_in']
        v_pin = 'd2u_out'
    elif 'u2d_in' in activity_dict:
        meas_pre += f"v{activity_dict['u2d_in'][2]}"
        v_key = 'u2d_in'
        v_tuple = activity_dict['u2d_in']
        v_pin = 'u2d_out'
    else:
        raise ValueError(f"Not a valid vertical input of short tile.")
    delay_h_meas = f"{meas_pre}_h_delay{suffix}"
    delay_v_meas = f"{meas_pre}_v_delay{suffix}"
    oslew_h_meas = f"{meas_pre}_h_o_slew{suffix}"
    oslew_v_meas = f"{meas_pre}_v_o_slew{suffix}"
    aVB_minus_aHL = v_tuple[0] - h_tuple[0]
    # Code below can be improved. No need to look up indices 4 times if 
    # the indices are shared
    h_delay = trilinear_interpolate(h_tuple[1], v_tuple[1], aVB_minus_aHL, \
                                    timing_dict[delay_h_meas], timing_dict['tH_arr'], \
                                    timing_dict['tV_arr'], timing_dict['pd_arr'])
    v_delay = trilinear_interpolate(h_tuple[1], v_tuple[1], aVB_minus_aHL, \
                                    timing_dict[delay_v_meas], timing_dict['tH_arr'], \
                                    timing_dict['tV_arr'], timing_dict['pd_arr'])
    h_oslew = trilinear_interpolate(h_tuple[1], v_tuple[1], aVB_minus_aHL, \
                                    timing_dict[oslew_h_meas], timing_dict['tH_arr'], \
                                    timing_dict['tV_arr'], timing_dict['pd_arr'])
    v_oslew = trilinear_interpolate(h_tuple[1], v_tuple[1], aVB_minus_aHL, \
                                    timing_dict[oslew_v_meas], timing_dict['tH_arr'], \
                                    timing_dict['tV_arr'], timing_dict['pd_arr'])
    # Postive unateness of both short and unit cell
    return {h_pin:(h_delay, h_oslew, h_tuple[2]), v_pin:(v_delay, v_oslew, v_tuple[2])}
  
def get_forward(activity_dict, cell_type, cell_dict, coupling=0):
    if cell_type == 'enable_tile':
        return get_forward_enable(activity_dict, cell_type, cell_dict)
    else:
        return get_forward_sh_uc(activity_dict, cell_type, cell_dict, coupling)

def timing_parse(fname):
    # Timing file is assumed to not have PG information
    with open(fname) as f:
        cell_dict = {}
        for line in f:
            line_arr = line.split()
            # Using # for comments in timing file
            if len(line_arr) == 0 or line_arr[0][0] == '#':
                continue
            if line_arr[0] == 'cell':
                cell_name = line_arr[1][1:-1] #excluding parantheses
                ip, op, d, tran, unateness, trig_grp, targ_grp, timing_dict = get_cell(cell_name, f)
                cell_data = {}
                cell_data['inputs']          = ip
                cell_data['outputs']         = op
                cell_data['nominal_delay']   = d
                cell_data['nominal_op_tran'] = tran
                cell_data['unateness']       = unateness
                cell_data['trigger_groups']  = trig_grp
                cell_data['target_groups']   = targ_grp
                cell_data['timing_dict']     = timing_dict
                cell_dict[cell_name] = cell_data
    return cell_dict
                
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--timing', type=str, required=True, help="INPUT TIMING FILE")
    args = parser.parse_args()
    cell_dict = timing_parse(args.timing)
    for cell in cell_dict:
        print(cell)
        print(cell_dict[cell].keys())#['target_groups'])#,": ", cell_dict[cell])
        print(cell_dict[cell]['timing_dict'].keys())#,": ", cell_dict[cell])
        for k in cell_dict[cell]['timing_dict']:
            a = np.array(cell_dict[cell]['timing_dict'][k])
            print(f"{k} {a.shape}")
    #a = get_forward({'in_':(88e-12, 38.2e-12, 'f', 'neta')}, 'enable_tile', cell_dict)
    #b = get_forward({'enable':(7.6e-11, 45.4e-12, 'r', 'netb')}, 'enable_tile', cell_dict)
    #print(a, b)
    #c = get_forward({'l2r_in':(121e-12, 44e-12, 'r', 'netc'), 'd2u_in':(65e-12, 51.2e-12, 'r','netd')}, 'short_tile', cell_dict)
    #print(c)
    ##c = get_forward({'l2r_in':(121e-12, 44e-12, 'r', 'netc'), 'd2u_in':(65e-12, 51.2e-12, 'f','netd')}, 'short_tile', cell_dict)
    ##print(c)
    #c = get_forward({'l2r_in':(121e-12, 44e-12, 'r', 'netc'), 'd2u_in':(65e-12, 51.2e-12, 'f','netd')}, 'unit_coupling_tile', cell_dict, 1)
    #print(c)
    #c = get_forward({'l2r_in':(121e-12, 44e-12, 'r', 'netc'), 'd2u_in':(65e-12, 51.2e-12, 'r','netd')}, 'unit_coupling_tile', cell_dict, 1)
    #print(c)
    #c = get_forward({'l2r_in':(121e-12, 44e-12, 'r', 'netc'), 'd2u_in':(65e-12, 51.2e-12, 'f','netd')}, 'unit_coupling_tile', cell_dict, -1)
    #print(c)
    #c = get_forward({'l2r_in':(121e-12, 44e-12, 'r', 'netc'), 'd2u_in':(65e-12, 51.2e-12, 'r','netd')}, 'unit_coupling_tile', cell_dict, -1)
    #print(c)
