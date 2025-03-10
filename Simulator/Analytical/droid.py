from timing_parse import timing_parse
from netlist_parse import netlist_parse
from Event import Event 
from Enable import Enable
from Short import Short
from Unit import Unit
from Interpolation import linear_interpolation, trilinear_interpolation, interpolate_for_outside_window
import numpy as np
from sortedcontainers import SortedSet
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import time

TOLERANCE = 0.5e-12

def set_tolerance(tol):
    TOLERANCE = tol
    print(f"Synchronization Tolerance changed to {tol}.")

def build_timing(fpath, quiet=True):
    cell_dict = timing_parse(fpath)
    for cell in cell_dict:
        if cell == 'enable_tile':
            Enable.set_timing_dict(cell_dict[cell]['timing_dict'], quiet=False)
        elif cell == 'short_tile':
            Short.set_timing_dict(cell_dict[cell]['timing_dict'], quiet=False)
        elif cell == 'unit_coupling_tile':
            Unit.set_timing_dict(cell_dict[cell]['timing_dict'], quiet=False)
    if not quiet:
        Enable.show_timing_dict()
        Short.show_timing_dict()
        Unit.show_timing_dict()

def get_period_dict(e:Event, period_dict:dict):
    if e.netname in period_dict:
        # Period is calculated rise to rise
        if e.transition == 'r':
            last_r = period_dict[e.netname][1]
            if last_r is not None:
                period_dict[e.netname][0] = e.arrival_time - last_r
            period_dict[e.netname][1] = e.arrival_time
    return

def check_convergence(e:Event, RefNet:str, period_dict:dict, cycle_num:int, tolerance:float=0.5e-12, quiet=True):
    # Check convergence whenever RefNet sees a falling transition
    converged = False
    periods = []
    if e.netname == RefNet:
        if e.transition == 'f':
            cycle_num += 1
            if not quiet: print(f"Cycle = {cycle_num}")
            for net in period_dict:
                # return if a period for any net in period_dict is not available
                if period_dict[net][0] is None:
                    return converged, cycle_num
                # else
                periods.append(period_dict[net][0])
            periods = np.array(periods)
            range_p = abs(np.max(periods) - np.min(periods))
            if range_p < tolerance:
                converged = True
            if not quiet: print(f"Range = {range_p}, tol = {tolerance}, Converged = {converged}")
    return converged, cycle_num 

def process_event(event:Event, pendingTrig:dict, Net2LastTran_dict:dict, Net2Event_dict: dict, Inst2Obj_dict:dict, \
                  Net2Inst_dict:dict, priority_queue:SortedSet, measureInst_dict:dict, period_dict:dict, RefNet:str, \
                  cycle_num:int, event_log:list, logfile, log:bool=False):
    # Given an event on a net, find which instance the net is connected to
    inst_names_list = set(Net2Inst_dict[event.netname])
    pending_status = False
    rm_event_set = set()
    output_event_list = []
    for inst_name in inst_names_list:
        inst_obj = Inst2Obj_dict[inst_name]
        # Operate only if the net is an input to the instance
        if inst_obj.is_input(event.netname):
            # If the instance is an Enable cell, process event as it is easy
            # Or if it is a coupling cell with coupling_val of 0
            if isinstance(inst_obj, Enable):
                # Get output event(s) 
                output_event_list = inst_obj.get_output_events(event)
                rm_event_set.add(event)
            # If a Coupling cell 
            else:
                #if inst_obj.coupling_val != 0:
                assoc_net, assoc_event = find_assoc_event(event, inst_obj, priority_queue, Net2Event_dict, logfile, log)
                if assoc_net is not None:
                    # if an associated net is found
                    if assoc_event is not None:
                        if log:
                            logfile.write(f"{assoc_event} associated with {event} as they are both inputs to {inst_name}.\n")
                        # if an event is found on the net 
                        if abs(assoc_event.arrival_time - event.arrival_time) > inst_obj.get_window():
                            # if the event occurs outside the window
                            # calculate next event on the basis of last tran
                            if log:
                                logfile.write(f"{assoc_event} does not interact with {event} as their arrival times are not within {inst_obj.get_window()}. Processing {event} only.\n")
                            if isinstance(inst_obj, Short):
                                output_event_list = inst_obj.get_output_events(event, assoc_event)
                                rm_event_set.add(event)
                                rm_event_set.add(assoc_event)
                                #raise NotImplementedError(f"Short cell needs to handle events outside window.")
                            else:
                                output_event_list = inst_obj.get_output_events(event, (assoc_net, Net2LastTran_dict[assoc_net][2]))
                                rm_event_set.add(event)
                        else:
                            # calculate output events using two events
                            if log:
                                logfile.write(f"{assoc_event} interacts with {event} as their arrival times are within {inst_obj.get_window()}.\n")
                            output_event_list = inst_obj.get_output_events(event, assoc_event)
                            rm_event_set.add(event)
                            rm_event_set.add(assoc_event)
                    else:
                        if log:
                            logfile.write(f"No event associated with {event} on instance {inst_name}.\n")
                        # event on assoc_net not found
                        # Start tracing backwards
                        left = max(0, event.arrival_time - inst_obj.get_window())
                        right= event.arrival_time + inst_obj.get_window()
                        #ret_val = get_trigger_relationship(assoc_net, (left, right), event.arrival_time, pendingTrig, Net2Inst_dict, Inst2Obj_dict, Net2Event_dict, logfile, log)
                        ret_val = get_trigger_relationship(assoc_net, (left, right), left, pendingTrig, Net2Inst_dict, Inst2Obj_dict, Net2Event_dict, logfile, log)
                        if log:
                            logfile.write(f"{event.netname}: {ret_val}\n")
                        if ret_val is not None:
                            if assoc_net not in pendingTrig:
                                pendingTrig[assoc_net] = event.netname
                            pending_status = True
                        else:
                            # ret_val is None but the instance is a Short Cell
                            if isinstance(inst_obj, Short):
                                # No event on the associated net or its predecessors in the Queue or pending dict
                                # Cannot process Short Cell with just one event so stall anyway.
                                if assoc_net not in pendingTrig:
                                    pendingTrig[assoc_net] = event.netname
                                pending_status = True
                            else:
                                output_event_list = inst_obj.get_output_events(event, (assoc_net, Net2LastTran_dict[assoc_net][2]))
                                rm_event_set.add(event)
                        # logfile.write(f"Pending triggers: {pendingTrig}\n")
                else:
                    if log:
                        logfile.write(f"{event} on backward path of instance {inst_name}.\n")
                    # assoc_net not found, not a net on interacting pins
                    # can schedule next event just from one event
                    output_event_list = inst_obj.get_output_events(event)
                    rm_event_set.add(event)
                #else:
                #    logfile.write(f"{inst_obj} does not have coupling enabled.\n")
                #    logfile.write(f"{assoc_net}\n")
                #    # The matrix for J=0 will have values that do not depend on the assoc_net's slew/arrival
                #    output_event_list = inst_obj.get_output_events(event, (assoc_net, Net2LastTran_dict[assoc_net][2]))
                #    rm_event_set.add(event)
            
            # Get output event(s) 
            for e in output_event_list:
                priority_queue.add((e.arrival_time, e.netname))
                Net2Event_dict[e.netname] = e
                if log:
                    logfile.write(f"{event} caused {e}\n")
            # Look for pending triggers
            list_of_trigs = []
            for trig_net in pendingTrig:
                if trig_net in Net2Event_dict:
                    if log:
                        logfile.write(f"{trig_net} is a pending trigger. Will trigger a pending event on {pendingTrig[trig_net]}\n")
                    list_of_trigs.append(trig_net)
            for tnet in list_of_trigs:
                # Look for event in Net2Event and add to priority queue
                pending_e = Net2Event_dict[pendingTrig[tnet]]
                priority_queue.add((pending_e.arrival_time, pending_e.netname))
                # delete the key value pair from pendingTrig
                del pendingTrig[tnet]
    # Remove the net and event from map IF EVENT WAS PROCESSED
    # IF ADDED TO PENDING LIST, DO NOT remove
    converged = False
    period_range = None
    if not pending_status:
        for rm_e in rm_event_set:
            for inst_name in inst_names_list:
                inst_obj = Inst2Obj_dict[inst_name]
                if isinstance(inst_obj, Unit) and inst_name in measureInst_dict:
                    inst_obj.record(rm_e)
            c, cycle_num = check_convergence(rm_e, RefNet, period_dict, cycle_num, TOLERANCE)
            converged = converged or c # rm_event_set can have multiple events, but only one of those on RefNet
            # Update period
            get_period_dict(rm_e, period_dict)
            # Update Last transition
            Net2LastTran_dict[rm_e.netname] = (rm_e.arrival_time, rm_e.slew, rm_e.transition)
            # Remove from dict
            removed_event = Net2Event_dict.pop(rm_e.netname)
            #if log:
            if rm_e.netname in period_dict:
                event_log.append(removed_event)
            # event_log.append(removed_event)           # populate event_log even if log is false
            rm_tuple = (rm_e.arrival_time, rm_e.netname)
            # remove from queue
            if rm_tuple in priority_queue:
                priority_queue.remove(rm_tuple)
    return converged, cycle_num

def find_assoc_event(event:Event, inst_obj, priority_queue:SortedSet, Net2Event_dict:dict, logfile, log=False):
    assoc_net = inst_obj.get_assoc_net(event.netname, logfile, log)
    # logfile.write(f"{assoc_net}, {event.netname}\n")
    assoc_event = None
    if assoc_net is not None:
        if assoc_net in Net2Event_dict:
            assoc_event =  Net2Event_dict[assoc_net]
    return assoc_net, assoc_event

def get_trigger_relationship(netname, window, threshold, pendingDict:dict, Net2Inst_dict:dict, Inst2Obj_dict:dict, Net2Event_dict:dict, logfile, log):
    if log:
        logfile.write(f"Checking for events on {netname} in {window}.\n")
    inst_list = find_instances_to_which_net_is_output(netname, Net2Inst_dict, Inst2Obj_dict)
    # okay to use inst_list[0] as a net can be output from only one instance
    if len(inst_list) == 0:
        if netname in Net2Event_dict:
            n_e = Net2Event_dict[netname]
            if n_e.arrival_time >= window[0] and n_e.arrival_time <= window[1]:
                # event could cause a transition
                if log:
                    logfile.write(f"Primary input {netname} has  event: '{n_e}' in {window}.\n")
                return window
            else:
                # independent of this event
                return None
        else:
            return None
    inst_obj = Inst2Obj_dict[inst_list[0]]
    #causal_nets = inst_obj.trace_causal_nets(netname)
    causal_nets = inst_obj.trace_causal_nets_modified(netname)
    #if netname in pendingDict:
    #    if log: logfile.write(f"{netname} is a pending trigger. Assume that it will affect.\n") 
    #    return window
    #el
    if window[1] < threshold:
        if log: logfile.write(f"{window[1]} < {threshold}. looked back far enough.\n") 
        return None
    else:
        #logfile.write(f"{netname} in pendingDict as pending event? {netname in pendingDict.values()}\n")
        #logfile.write(f"{netname} in pendingDict as trigger? {netname in pendingDict}\n")
        if netname in Net2Event_dict:
            n_e = Net2Event_dict[netname]
            if n_e.arrival_time >= window[0] and n_e.arrival_time <= window[1]:
                # event could cause a transition
                # need to add a trigger relationship
                if log:
                    logfile.write(f"{netname} has  event: '{n_e}' in {window}.\n")
                return window
            else:
                # independent of this event
                return None
        #elif netname in pendingDict:
        #    return window
        else:
            # look at predecessors
            trig_rel = {}
            direction = 'F'
            pts = inst_obj.net2ports[netname]
            if 'r2l_out' in pts or 'u2d_out' in pts:
                direction = 'B'
            if log: logfile.write(f"{netname} connected to {pts} of {inst_obj.instance_name}. Calc window from {direction} path.\n")
            derived_window = (max(0, window[0] - inst_obj.get_max_delay(direction)), window[1] - inst_obj.get_min_delay(direction))
            for net in causal_nets:
                ret_val = get_trigger_relationship(net, derived_window, threshold, pendingDict, Net2Inst_dict, Inst2Obj_dict, Net2Event_dict, logfile, log)
                trig_rel[net] = ret_val
                if log:
                    logfile.write(f"{net} : {ret_val}\n")
            all_none = True
            min_net = None
            min_window = None
            for net in trig_rel:
                if trig_rel[net] is not None:
                    all_none = False
                    if min_window is None:
                        min_net = net
                        min_window = trig_rel[net]
                    else:
                        if min_window[1] < trig_rel[net][1]:
                            min_net = net
                            min_window = trig_rel
            if all_none == False:
                if log:
                    logfile.write(f"All none for {netname}\n")
                # Commented 2 lines below because process_event called get_trigger_relationship 
                # with an empty dict for pendingDict
                #if min_net not in pendingDict:
                #    pendingDict[min_net] = netname
                # else:
                #     raise ValueError(f"{min_net} already used as a trigger for {pendingDict[min_net]}. Trying to use it to trigger event on {netname} as well!")
                return window
            else:
                return None

def find_instances_to_which_net_is_output(netname, Net2Inst_dict:dict, Inst2Obj_dict:dict):
    inst_list = Net2Inst_dict[netname]
    ret_list = []
    for inst_name in inst_list:
        inst_obj = Inst2Obj_dict[inst_name]
        if inst_obj.is_output(netname):
            ret_list.append(inst_name)
    return ret_list

def build_cell_objects(fpath, coupling_dict, noise_on=False, three_sig_per_stage=None):
    subckt_dict, instance_dict, net2instance_name_dict = netlist_parse(fpath, ['vdd', 'vss'])
    name2obj_dict = {}
    for instance_name in instance_dict:
        cell_type, port_map = instance_dict[instance_name]
        if cell_type == 'enable_tile':
            obj = Enable(instance_name, port_map, noise_on=False)
            name2obj_dict[instance_name] = obj
        elif cell_type == 'unit_coupling_tile':
            obj = Unit(instance_name, port_map, coupling_dict[instance_name], noise_on=noise_on, three_sig=three_sig_per_stage) 
            name2obj_dict[instance_name] = obj
        elif cell_type == 'short_tile':
            obj = Short(instance_name, port_map)
            name2obj_dict[instance_name] = obj
    
    return name2obj_dict, net2instance_name_dict

def build_coupling_dict(J):
    size = J.shape[0]
    coupling_dict = {}
    measureInst_dict = {}
    for x in range(size):
        for y in range(size):
            i = (size - x - 1)*size + y
            coupling_dict[f'xi{i}'] = J[x][y]
            if x == 0 and y!=0:
                measureInst_dict[f'xi{i}'] = y
    return coupling_dict, measureInst_dict

def assign_spins(measureInst_dict, Inst2Obj_dict, period_dict, Osc2Net):
    sol = {}
    sol[0] = 1
    for inst_name in measureInst_dict:
        inst_obj = Inst2Obj_dict[inst_name]
        osc = measureInst_dict[inst_name]
        if isinstance(inst_obj, Unit):
            prd = period_dict[Osc2Net[osc]][0]
            #if prd is None: print(Osc2Net[osc], osc, period_dict[Osc2Net[osc]])
            #print(f"PD = {inst_obj.arrival_diff}, prd = {prd}")
            if inst_obj.arrival_diff < 0.25*prd or inst_obj.arrival_diff > 0.75*prd:
                sol[osc] = 1
            else:
                sol[osc] =-1
    return sol

def ham_from_sol(J, sol):
    prod_of_spins = np.zeros((len(sol),len(sol)))
    for i in sol:
        for j in sol:
            if i != j:
                prod_of_spins[i][j] = sol[i]*sol[j]
            else:
                prod_of_spins[i][j] = 0
    
    return -1*np.sum(np.multiply(J,prod_of_spins))

def local_search(J, sol, best_ham = None):
    # one spin at a time flip search
    if best_ham is None:
        best_ham = ham_from_sol(J, sol)
    best_sol = sol
    for idx in sol:
        t_sol = sol
        t_sol[idx] = -1*sol[idx]
        local_ham = ham_from_sol(J, sol)
        if local_ham < best_ham:
            best_ham = local_ham
            best_sol = t_sol
    return best_ham, best_sol

def plot_events(event_log, instance_set, Net2Inst_dict, Inst2Obj_dict):
    inst_to_fig = {}
    width = 1e-12
    arrow_width = 10e-12
    arrow_length = 0.1
    arrow_color1 = 'blue'
    arrow_color2 = 'red'

    for inst_name in instance_set:
        f, ax = plt.subplots(1)
        inst_to_fig[inst_name] = f
        inst_obj = Inst2Obj_dict[inst_name]
        ax.set_title(f"{inst_name}")
        # https://stackoverflow.com/questions/39500265/how-to-manually-create-a-legends
        clr1_patch = mpatches.Patch(color=arrow_color1, label=f"l2r_in:{inst_obj.port2net['l2r_in']}")
        clr2_patch = mpatches.Patch(color=arrow_color2, label=f"d2u_in:{inst_obj.port2net['d2u_in']}")
        ax.legend(handles=[clr1_patch, clr2_patch])
    # fig, ax1 = plt.subplots(1, sharex=True)
    
    for e in event_log:
        inst_list = set(Net2Inst_dict[e.netname])
        for inst_name in inst_list:
            if inst_name in instance_set:
                inst_obj = Inst2Obj_dict[inst_name]
                fig = inst_to_fig[inst_name]
                [ax] = fig.axes
                if inst_obj.port2net['l2r_in'] == e.netname:
                    if e.transition == 'r':
                        ax.arrow(e.arrival_time, 0, 0, 1, width=width, head_width=arrow_width, head_length=arrow_length, fc=arrow_color1, ec=arrow_color1, length_includes_head=True)
                    elif e.transition == 'f':
                        ax.arrow(e.arrival_time, 1, 0,-1, width=width, head_width=arrow_width, head_length=arrow_length, fc=arrow_color1, ec=arrow_color1, length_includes_head=True)
                    ax.fill_between([e.arrival_time - inst_obj.get_window(), e.arrival_time + inst_obj.get_window()],
                                     [0, 0], [1,1], color='b', alpha=0.2)
                if inst_obj.port2net['d2u_in'] == e.netname:
                    if e.transition == 'r':
                        ax.arrow(e.arrival_time,-1, 0, 1, width=width, head_width=arrow_width, head_length=arrow_length, fc=arrow_color2, ec=arrow_color2, length_includes_head=True)
                    elif e.transition == 'f':
                        ax.arrow(e.arrival_time, 0, 0,-1, width=width, head_width=arrow_width, head_length=arrow_length, fc=arrow_color2, ec=arrow_color2, length_includes_head=True)
                    ax.fill_between([e.arrival_time - inst_obj.get_window(), e.arrival_time + inst_obj.get_window()],
                                     [-1, -1], [0,0], color='r', alpha=0.2)

def log_period(event_log, net_set, write_file=None, plotfig=False, res=0.1e-12, print_every_ncycles=5):
    if write_file is None and plotfig == False:
        return
    if plotfig: fig, ax = plt.subplots()
    netwise_log = {}
    for e in event_log:
        if e.netname in net_set:
            if e.netname not in netwise_log:
                netwise_log[e.netname] = []
            net_log = netwise_log[e.netname]
            net_log.append(e.arrival_time)
    import pandas as pd
    df = pd.DataFrame({})
    for net in netwise_log:
        net_log = netwise_log[net]
        x = []
        y = []
        for i in range(0,len(net_log)-2):
            x.append(net_log[i+2])
            prd = net_log[i+2]-net_log[i]
            y.append(prd)
        df.insert(len(df.columns), f'{net}_x', pd.Series(x)) 
        df.insert(len(df.columns), f'{net}_y', pd.Series(y)) 
        if plotfig: ax.plot(x, y, '-', label=f'{net}')
    df_cleaned = df.dropna()
    df_cleaned = (df_cleaned/res).round()*res # resolution
    # Print resolution, 2 lines per cycles 
    df_cleaned = df_cleaned[df_cleaned.index % (2*print_every_ncycles) == 1]
    if plotfig:
        if len(net_set) < 15:
            ax.legend()
    if write_file is not None:
        df_cleaned.to_csv(write_file, mode='a', index=False)

def invert(c):
    if c == 'r':
        return 'f'
    else:
        return 'r'

def populate_last_tran_neg_unate(initial_events, Net2Inst_dict, Inst2Obj_dict, size=5):
    # inst names are regular
    Net2LastTran_dict = {}
    for net in initial_events:
        Net2LastTran_dict[net] = (None, None, 'f')
    for c in range(size):
        for r in range(size):
            inst_name = f'xi{r*size+c}'
            inst_obj = Inst2Obj_dict[inst_name]
            #print(inst_name, inst_obj.port2net)
            if c % 2 == 0:
                Net2LastTran_dict[inst_obj.port2net['l2r_in']] = (None, None, 'r')
                Net2LastTran_dict[inst_obj.port2net['r2l_in']] = (None, None, 'f')
            else:
                Net2LastTran_dict[inst_obj.port2net['l2r_in']] = (None, None, 'f')
                Net2LastTran_dict[inst_obj.port2net['r2l_in']] = (None, None, 'r')
            if r % 2 == 0:
                Net2LastTran_dict[inst_obj.port2net['d2u_in']] = (None, None, 'r')
                Net2LastTran_dict[inst_obj.port2net['u2d_in']] = (None, None, 'f')
            else:
                Net2LastTran_dict[inst_obj.port2net['d2u_in']] = (None, None, 'f')
                Net2LastTran_dict[inst_obj.port2net['u2d_in']] = (None, None, 'r')
            if c % size == 0:
                Net2LastTran_dict[inst_obj.port2net['r2l_out']] = (None, None, 'r')
            if r % size == 4:
                Net2LastTran_dict[inst_obj.port2net['u2d_out']] = (None, None, 'r')
    #print(Net2LastTran_dict)
    return Net2LastTran_dict

def random_initial_events(l, period):
    # Return two dicts: one maps enable nets to starting events,
    # the other maps enable nets to oscillator index
    events = {}
    en2osc = {}
    # Random seeds needed for multiprocessing, without this Numpy used same seed for all child processes
    np.random.seed()
    phi = np.random.randint(0, period, l)
    for i, p in enumerate(phi):
        events[f'enable<{i}>'] = (p*1e-12, 5e-12, 'r')
        en2osc[f'enable<{i}>'] = i
    #print(events)
    #print(en2osc)
    return events, en2osc

def sim(initial_events, en2osc, netlist_path, J, stopTime, noise_on=False, three_sig_per_osc=0, log=False, plot=False, logname=None, periodlogname=None):
    if logname is None:
        logname = time.strftime("logfile_%d%b%y_%H_%M_%S.txt")
    if plot:
        if periodlogname is None:
            prdlogname = time.strftime("period_%d%b%y_%H_%M_%S.txt")
        else:
            prdlogname = periodlogname
    else:
        prdlogname = None
    with open(logname, 'w') as logfile:
        logfile.write(time.strftime("%d %b %y %H:%M:%S\n"))
        best_ham, best_sol = sim_wrapper(initial_events, en2osc, netlist_path, J, stopTime, \
                                         logfile, noise_on, three_sig_per_osc, log=log, plot=plot, periodlogname=prdlogname)
    print(f"Log saved in {logname}")
    return best_ham, best_sol

def sim_wrapper(initial_events, en2osc, netlist_path, J, stopTime, logfile, noise_on=False, three_sig_per_osc=None, log=False, plot=False, periodlogname=None):
    logfile.write(f'Initial: {initial_events}\n')
    logfile.write(f'StopTime: {stopTime}\n')
    size, _ = J.shape
    coupling_dict, measureInst_dict = build_coupling_dict(J)
    logfile.write(f"{coupling_dict}\n")
    logfile.write(f"{measureInst_dict}\n")
    if noise_on:
        np.random.seed()
    if three_sig_per_osc is None:
        three_sig_per_stage = None
    else:
        # 2N independent events whose variances add up. sig_RO^2 = 2*N*(sig_stage^2)
        #three_sig_per_stage = three_sig_per_osc/np.sqrt(2*J.shape[0])
        # 2N correlated events whose deviations add up. sig_RO = 2*N*(sig_stage)
        three_sig_per_stage = three_sig_per_osc/(2*J.shape[0])
    Inst2Obj_dict, Net2Inst_dict = build_cell_objects(netlist_path, coupling_dict, noise_on, three_sig_per_stage)
    for inst_name in Inst2Obj_dict:
        cell_obj = Inst2Obj_dict[inst_name]
        #print(cell_obj)
    #"""
    # Instantiate the queue
    priority_queue = SortedSet()
    # Netname to last transition seen
    Net2LastTran_dict = {}
    # event log for plotting
    event_log = []
    # Netname to Event dict
    Net2Event_dict = {}
    # Pending trigger event dict
    pendingTrig = {}
    # Record period for convergence check
    period_dict = {}
    # Reference Net to count cycles
    RefNet = None
    # osc index to net
    Osc2Net = {}
    # Populate the Queue and the Net2Event dict
    for net in initial_events:
        a_t, slew, tran = initial_events[net]
        e = Event(net, a_t, slew, tran)
        Net2Event_dict[net] = e
        # Populate the priority queue with 2-tuple, arrival_time and netname
        priority_queue.add((a_t, net))
        inst_list = Net2Inst_dict[net]
        for inst_name in inst_list:
            inst_obj = Inst2Obj_dict[inst_name]
            if inst_obj.is_input(net):
                op = inst_obj.get_outputs()
                #first_elem = op[0]
                iterator = iter(op)
                first_elem = next(iterator)
                nname = inst_obj.port2net[first_elem]
                Osc2Net[en2osc[net]] = nname 
                period_dict[nname] = [None, None]
                if RefNet is None:
                    RefNet = nname
                # skip other instances, if any
                break

    logfile.write(f"osc2net: {Osc2Net}\n")
    #Net2Osc = {}
    #for i in Osc2Net:
    #    Net2Osc[Osc2Net[i]] = i
    
    # Populate LastTran dict
    #for n in Net2Inst_dict:
    #    if n in initial_events:
    #        Net2LastTran_dict[n] = (None, None, 'f')
    #    else:
    #        Net2LastTran_dict[n] = (None, None, 'r')
    Net2LastTran_dict = populate_last_tran_neg_unate(initial_events, Net2Inst_dict, Inst2Obj_dict, size)
    #input()
    
    cycle_num = 0
    converged_count = 0
    best_ham = 0
    best_sol = None
    best_local_ham = 0
    best_local_sol = None
    startT = time.perf_counter()
    while len(priority_queue) > 0:
        arrival_time, netname = priority_queue.pop(0)
        e = Net2Event_dict[netname]
        scheduleTarg = False
        if log:
            logfile.write(f"Processing {e}\n")
        last_cycle_num = cycle_num
        converged, cycle_num = process_event(e, pendingTrig, Net2LastTran_dict, Net2Event_dict, Inst2Obj_dict, \
                                  Net2Inst_dict, priority_queue, measureInst_dict, period_dict, RefNet, cycle_num, event_log, logfile, log)
        if last_cycle_num != cycle_num:
            if converged:
                converged_count += 1
            else:
                converged_count = 0
            if cycle_num % 50 == 0:
                #logfile.write(f"Cycle: {cycle_num}, Period_range:{period_range}\n")
                sol = assign_spins(measureInst_dict, Inst2Obj_dict, period_dict, Osc2Net)
                ham = ham_from_sol(J, sol)
                logfile.write(f"At cycle: {cycle_num}, Ham: {ham}, Sol: {sol}\n")
                if ham < best_ham:
                    best_ham = ham
                    best_sol = sol
                logfile.write(f"At cycle: {cycle_num}, BestHam: {best_ham}, BestSol: {best_sol}\n")
                lham, lsol = local_search(J, sol, ham)
                if lham < best_local_ham:
                    best_local_ham = lham
                    best_local_sol = lsol
                logfile.write(f"At cycle: {cycle_num}, BestLocalHam: {best_local_ham}, BestLocalSol: {best_local_sol}\n")

        if log:
            logfile.write(f"Queue is : {priority_queue}\n")
            #logfile.write(f"Net2LastTran : {Net2LastTran_dict}\n") #Huge dict, avoid printing
            logfile.write(f"PendingTrig : {pendingTrig}\n")
            logfile.write(f"-------------------------\n")
        if arrival_time > stopTime:
            if log:
                for n in Net2Event_dict:
                    logfile.write(f"{Net2Event_dict[n]}\n")
            sol = assign_spins(measureInst_dict, Inst2Obj_dict, period_dict, Osc2Net)
            ham = ham_from_sol(J, sol)
            logfile.write(f"Unconverged at: {cycle_num}, Ham: {ham}, Sol: {sol}\n")
            if ham < best_ham:
                best_ham = ham
                best_sol = sol
            logfile.write(f"At cycle: {cycle_num}, BestHam: {best_ham}, BestSol: {best_sol}\n")
            lham, lsol = local_search(J, sol, ham)
            if lham < best_local_ham:
                best_local_ham = lham
                best_local_sol = lsol
            logfile.write(f"At cycle: {cycle_num}, BestLocalHam: {best_local_ham}, BestLocalSol: {best_local_sol}\n")
            break
        if converged_count >= 5:
            sol = assign_spins(measureInst_dict, Inst2Obj_dict, period_dict, Osc2Net)
            ham = ham_from_sol(J, sol)
            logfile.write(f"Converged at: {cycle_num}, Ham: {ham}, Sol: {sol}\n")
            if ham < best_ham:
                best_ham = ham
                best_sol = sol
            logfile.write(f"At cycle: {cycle_num}, BestHam: {best_ham}, BestSol: {best_sol}\n")
            lham, lsol = local_search(J, sol, ham)
            if lham < best_local_ham:
                best_local_ham = lham
                best_local_sol = lsol
            logfile.write(f"At cycle: {cycle_num}, BestLocalHam: {best_local_ham}, BestLocalSol: {best_local_sol}\n")
            break

    endT = time.perf_counter()
    logfile.write(f"Time taken for simulation: {endT-startT}\n")
    if plot:
        # USE this
        with open(periodlogname, 'w') as f:
            f.write(f'# {Osc2Net}\n') # add a comment
        log_period(event_log, set(period_dict.keys()), write_file=periodlogname, res=0.1e-12, print_every_ncycles=5)
        plt.show()
    #"""
    return best_ham, best_sol

def read_init(fpath):
    init_events = {}
    en2osc = {}
    with open(fpath, 'r') as initfile:
        for line in initfile:
            line = line.rstrip()
            line_arr = line.split(',')
            init_events[f'enable<{line_arr[0]}>'] = (int(line_arr[-1])*1e-12, 35e-12, 'r')
            en2osc[f'enable<{line_arr[0]}>'] = int(line_arr[0])
    print(en2osc)
    return init_events, en2osc

def sim_mc_wrapper(netlist_path, stopTime, num_mc, size):
    import multiprocessing
    import os

    path = f'./test_flow_{size}_'+time.strftime("%d%b%y_%H_%M_%S"+'/')

    if not os.path.exists(path):
        os.makedirs(path)

    # LOAD TIMING INFO
    build_timing('timing_max7.txt')

    for d in ['0p2']:
    #for d in ['0p2', '0p4', '0p6', '0p8', '1p0']:
        path_d = path + f'{d}/'
        if not os.path.exists(path_d):
            os.makedirs(path_d)
        
        for i in range(2):
        #for i in range(10):
            path_d_i = path_d + f'prob_{i}/'
            if not os.path.exists(path_d_i):
                os.makedirs(path_d_i)
            if size == 32:
                rpath = f'/scratch/kumar663/GF12/sim/ising_32x32_max5/flow_{d}/prob_{i}/'
                period = 21000
            elif size == 50:
                rpath = f'/scratch/kumar663/GF12/sim/ising_50x50_max7/flow_{d}/prob_{i}/'
                period = 35000
            else:
                raise ValueError(f"Size unsupported right now.")

            processes = []
            for mc_run in range(num_mc):
                J = np.loadtxt(f'{rpath}/J_matrix.txt', dtype=int) 
                initial_events, en2osc = random_initial_events(size, period)
                process = multiprocessing.Process(target=sim, args=(initial_events, en2osc, netlist_path, J, stopTime, False, False, path_d_i+f'logfile_{mc_run}.txt'))
                processes.append(process)
                process.start()

            for process in processes:
                process.join()

def wrapper(size, period, rpath, netlist_path, stopTime, logfile_path, noise_on, three_sig_per_osc, prdfile_path):
    J = np.loadtxt(f'{rpath}/J_matrix.txt', dtype=int) 
    initial_events, en2osc = random_initial_events(size, period)
    return sim(initial_events, en2osc, netlist_path, J, stopTime, noise_on, three_sig_per_osc, 
               log=False, plot=True, logname=logfile_path, periodlogname=prdfile_path)

def wrapper_49(size, period, rpath, netlist_path, stopTime, logfile_path, noise_on, three_sig_per_osc):
    J = np.loadtxt(rpath, dtype=int) 
    row_of_zeros = np.zeros((1, J.shape[1]), dtype=int)
    J = np.concatenate((J, row_of_zeros), axis=0)
    column_of_zeros = np.zeros((J.shape[0], 1), dtype=int)
    J = np.concatenate((J, column_of_zeros), axis=1)
    np.fill_diagonal(J, 0)
    initial_events, en2osc = random_initial_events(size, period)
    return sim(initial_events, en2osc, netlist_path, J, stopTime, noise_on, three_sig_per_osc, False, False, logfile_path)

def error_callback(exception):
    print(f"Error: {exception}")

def sim_mc_wrapper_pool(netlist_path, stopTime, num_mc, size, d_arr, p_idx_arr):
    print(f"Confirm timing file is correct before runs finish.")
    print(f"Check synchronization tolerance.")
    print(f"Make sure to check the densities and problem arrays.")
    import multiprocessing as mp
    import os

    path = f'/scratch/kumar663/runtime_data/pool_flow_{size}_'+time.strftime("%d%b%y_%H_%M_%S"+'/')

    if not os.path.exists(path):
        print(f"Created {path}")
        os.makedirs(path)

    # LOAD TIMING INFO
    build_timing('timing_asap7.txt')

    #num_process = max(4, mp.cpu_count() - 8)
    num_process = 20
    #for d in ['0p2', '0p4', '0p6', '0p8', '1p0']:
    #for d in ['0.2', '0.4', '0.6', '0.8', '1.0']:
    pool = mp.Pool(processes=num_process)
    for d in d_arr:
        path_d = path + f'{d}/'
        if not os.path.exists(path_d):
            os.makedirs(path_d)
        
        #for i in range(10):
        for i in p_idx_arr:
            path_d_i = path_d + f'prob_{i}/'
            #path_d_i = path_d + f'rg_{i}/'
            if not os.path.exists(path_d_i):
                os.makedirs(path_d_i)
            if size == 32:
                # rpath = f'/scratch/kumar663/GF12/sim/ising_32x32_max7/flow_{d}/prob_{i}/'
                rpath = f'/home/sachin00/kumar663/scripts/android/runtime_data/32x32/{d}/prob_{i}'
                period = 1600
                set_tolerance(3.2e-12)
            elif size == 50:
                #rpath = f'/scratch/kumar663/GF12/sim/ising_50x50_max7/flow_{d}/prob_{i}/'
                #rpath = f'/home/grads/kumar663/scripts/android/random_graphs_49/density_{d}/rg_{i}.txt'
                rpath = f'/home/sachin00/kumar663/scripts/android/runtime_data/50x50/{d}/prob_{i}'
                period = 2500
                set_tolerance(5e-12)
            elif size == 20:
                rpath = f'/home/sachin00/kumar663/scripts/android/runtime_data/20x20/{d}/prob_{i}'
                period = 880
                set_tolerance(2e-12)
            elif size == 10:
                rpath = f'/home/sachin00/kumar663/scripts/android/runtime_data/10x10/{d}/prob_{i}'
                period = 440
                set_tolerance(1e-12)
            elif size == 5:
                rpath = f'/home/sachin00/kumar663/scripts/android/runtime_data/5x5/{d}/prob_{i}'
                period = 60
                set_tolerance(0.5e-12)
            else:
                raise ValueError(f"Size unsupported right now.")

            process = [pool.apply_async(wrapper, (size, period, rpath, netlist_path, stopTime, path_d_i+f'logfile_{mc_run}.txt', False, None, \
                                                  path_d_i+f'prd_log_{mc_run}.txt'), error_callback=error_callback) for mc_run in range(num_mc)]
            #with mp.Pool(processes=num_process) as pool:
            #    ##J = np.loadtxt(f'{rpath}/J_matrix.txt', dtype=int) 
            #    ##initial_events, en2osc = random_initial_events(size, period)
            #    ## No noise run
            #    ##sim(initial_events, en2osc, netlist_path, J, stopTime, True, 0.05*period*1e-12, False, False, path_d_i+f'no_noise.txt')
            #    ##process = [pool.apply_async(sim, (initial_events, en2osc, netlist_path, J, stopTime, True, 0.05*period*1e-12, \
            #    ##                            False, False, path_d_i+f'noise_{mc_run}.txt')) for mc_run in range(num_mc)]
            #    process = [pool.apply_async(wrapper, (size, period, rpath, netlist_path, stopTime, \
            #                                          path_d_i+f'logfile_{mc_run}.txt', False, None)) for mc_run in range(num_mc)]
            #    #process = [pool.apply_async(wrapper_49, (size, period, rpath, netlist_path, stopTime, \
            #    #                                         path_d_i+f'logfile_{mc_run}.txt', False, None)) for mc_run in range(num_mc)]
            #    pool.close()
            #    pool.join()
    pool.close()
    pool.join()

if __name__ == '__main__':
    build_timing('./data/timing_asap7.txt', quiet=True)
    J = np.loadtxt('./data/problems/1.0/prob_0/J_matrix.txt', dtype=int)
    
    okay = 0
    val_err = 0
    ni_err = 0
    runs = 1
    log = False
    for i in range(runs):
        initial_events, en2osc = random_initial_events(50, 100)
        try:
            sim(initial_events=initial_events,          # Initial events at enable pins 
                en2osc=en2osc,                          # Map enable pins to ROs
                netlist_path='./data/ising_50x50.sp',   # Path to netlist
                J=J,                                    # Path to coupling matrix
                stopTime=300e-9,                        # Simulation stop time 
                log=log,                                # Enable/disable detailed logging
                logname='dbg_50.txt',                   # Path to logfile 
                )
        except ValueError as verr:
            val_err += 1
            print(f"ValueError for {initial_events}.")
            print(f"{verr}")
        except NotImplementedError as nierr:
            ni_err += 1
            print(f"NotImplementedError for {initial_events}.")
            print(f"{nierr}")
        else:
            okay += 1
            #print(f"Okay for {initial_events}.")
    print(f"{okay} out of {runs} threw no error. {val_err} had ValueError and {ni_err} had NotImplementedError.")
