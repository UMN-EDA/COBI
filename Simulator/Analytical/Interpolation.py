
def find_index_binary_search(sorted_list, target):
    # List is sorted in ASCENDING ORDER
    # ASSUMES target >= minimum and <= maximum
    low = 0 
    high = len(sorted_list) - 1 
    left_index = -1

    # Finding the left index
    while low <= high:
        mid = (low + high) // 2  # Calculate the middle index
        if sorted_list[mid] <= target:
            low = mid + 1 
            left_index = mid 
        else:
            high = mid - 1 

    return left_index

def get_indices(tH, tH_arr, tV, tV_arr, pd, phase_diff_arr):
    if tH < tH_arr[0] or tH > tH_arr[-1]: # assumes tH_arr is sorted in inc order
        raise ValueError(f"First coordinate {tH} out of array.")
    if tV < tV_arr[0] or tV > tV_arr[-1]: # assumes tv_arr is sorted in inc order
        raise ValueError(f"Second coordinate {tV} out of array.")
    hidx_lt = find_index_binary_search(tH_arr, tH)
    vidx_lt = find_index_binary_search(tV_arr, tV)
    if pd < phase_diff_arr[0]:
        pdidx_lt = 0 
    elif pd > phase_diff_arr[-1]:
        pdidx_lt = len(phase_diff_arr)-2 
    else:
        pdidx_lt = find_index_binary_search(phase_diff_arr, pd)
        if pdidx_lt == -1:
            raise ValueError(f"Phase diff {pd} not found in {phase_diff_arr}.")
    # Precalc tH_d, tV_d etc and 1-tH_d etc
    

def trilinear_interpolation(tH, tV, pd, matrix, tH_arr, tV_arr, phase_diff_arr):
    if tH < tH_arr[0] or tH > tH_arr[-1]: # assumes tH_arr is sorted in inc order
        raise ValueError(f"First coordinate {tH} out of array.")
    if tV < tV_arr[0] or tV > tV_arr[-1]: # assumes tv_arr is sorted in inc order
        raise ValueError(f"Second coordinate {tV} out of array.")

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
        pdidx_lt = find_index_binary_search(phase_diff_arr, pd)
        if pdidx_lt == -1:
            raise ValueError(f"Phase diff {pd} not found in {phase_diff_arr}.")
        #for pdidx in range(0, len(phase_diff_arr)-1):
        #    if pd >= phase_diff_arr[pdidx] and pd <= phase_diff_arr[pdidx+1]:
        #        pdidx_lt = pdidx
        #        break
    tH_d = (tH - tH_arr[hidx_lt])/(tH_arr[hidx_lt+1] - tH_arr[hidx_lt])
    tV_d = (tV - tV_arr[vidx_lt])/(tV_arr[vidx_lt+1] - tV_arr[vidx_lt])
    pd_d = (pd - phase_diff_arr[pdidx_lt])/(phase_diff_arr[pdidx_lt+1] - phase_diff_arr[pdidx_lt])

    #print(type(hidx_lt), type(vidx_lt), type(pdidx_lt))
    #print(type(matrix))
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
    #print(c)
    return c

#def trilinear_interpolation(tH, tV, pd, matrix, tH_arr, tV_arr, phase_diff_arr):
def interpolate_for_outside_window(tX, tX_arr, direction, matrix):
    #direction == 'h' or 'v'
    if tX < tX_arr[0] or tX > tX_arr[-1]:
        raise ValueError(f"Slew of {tX} is outside the array given.")
    for idx in range(0, len(tX_arr)-1):
        if tX_arr[idx] <= tX and tX_arr[idx+1] >= tX:
            idx_lt = idx
            break
    #idx_lt = 
    if direction == 'h':
        # last tran at vertical node must have been earlier, aV_minus_aH < 0
        # slew of event at vertical net should not matter, using any index should be fine, using 0 here
        l = matrix[idx_lt,   0, 0]
        r = matrix[idx_lt+1, 0, 0]
    elif direction == 'v':
        # last tran at horizontal node must have been earlier, aV_minus_aH > 0
        # slew of event at horizontal net should not matter, using any index should be fine, using 0 here
        l = matrix[0, idx_lt,   -1]
        r = matrix[0, idx_lt+1, -1]
    x_d = (tX- tX_arr[idx_lt])/(tX_arr[idx_lt+1]-tX_arr[idx_lt])
    y = l*(1-x_d) + r*x_d
    return y


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

