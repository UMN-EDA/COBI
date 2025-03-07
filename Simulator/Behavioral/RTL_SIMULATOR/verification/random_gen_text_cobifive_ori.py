import numpy as np
from dwave_qbsolv import QBSolv
import argparse
import dimod
import os

def transfer(m):
    str_value='ECA864203579BDF'
    dict_data={}
    for i in range(15):
        dict_data[i-7]=str_value[i]
    if m in list(dict_data.keys()):
        return(dict_data[m])
    else:
        raise ValueError(f"{m} not in dict")

def rev(m):
    str_value='ECA864203579BDF'
    if m in str_value:
        return str_value.index(m)-7
    else:
        raise ValueError(f"{m} not in dict")

def transfer_with_spins(m_str, spins):
    if len(m_str)!= len(spins):
        raise ValueError(f"length do not match!{len(m_str)} {len(spins)}")
    spin1_list = ['0', 'X', 'F', '1', 'E', '2', 'D', '3', 'C', '4', 'B', '5', 'A', '6', '9', '7']
    spin0_list = ['0', 'X', '1', 'F', '2', 'E', '3', 'D', '4', 'C', '5', 'B', '6', 'A', '9', '7']
    output_str = ''
    for i,m in enumerate(m_str):
        if int(m, 16) == 1:
            raise ValueError(f"'1' is illegal in input str!")
        elif spins[i] == 1:
            output_str += spin1_list[int(m, 16)]
        elif spins[i] == 0:
            output_str += spin0_list[int(m, 16)]
        else:
            raise ValueError(f"Spin should be 0 or 1! {spin}")
    return output_str
        
def test():
    path_test = f"/home/chriskim00/cobieval/DEMO_FOLDER/Simulator/Behavioral/RTL_SIMULATOR/txt/data_1_v.txt"
    memory_row=[]
    memory_col=[]
    with open(path_test,'r') as fp:
        lines = fp.readlines()
    for i,line in enumerate(lines):
        if i<46:
            memory_row.append(line[0:-1])
        else:
            memory_col.append(line[0:-1])
        line_half1 = line[0:23]
        line_half2 = line[23:-1]

    J = []
    for row in memory_row:
        transferred_row=[]
        for char in row:
            transferred_row.append(rev(char))
        J.append(transferred_row)

    J = []
    for row in memory_row:
        transferred_row = []
        for char in row:
            transferred_row.append(rev(char))
        J.append(transferred_row)
    J = np.array(J,dtype=int)

    J = np.flipud(J)
    J_dict = {}
    for i in range(46):
        for j in range(i):
            J_dict[(i, j)]=0
        for j in range(i,46):
            J_dict[(i,j)] = J_dict.get((i,j), 0) + J[i,j] + J[j,i]
    
    J_dict = {k: -v for k, v in J_dict.items()}
    opposite_J = [-x for x in J]
    qbsolve = QBSolv()
    response = qbsolve.sample_ising ({},-J)
    print(f"QB Energy: {response.data_vectors['energy']}")
    reference_list = response.samples()[0]
    list_ref = []
    for i in range(len(reference_list)):
        list_ref.append(int((1+reference_list[i])/2))
    
    for i,line in enumerate(lines):
        line_half1 = line[0:23]
        line_half2 = line[23:-1]
        sum1=transfer_with_spins(line_half1,list_ref[0:23])
        sum2=transfer_with_spins(line_half2,list_ref[23:])

    #ori_spin1 = [0,1,1,0,1,0,1,0,1,0,1,1,0,0,0,1,0,1,0,0,0,1,1,0,1,0,0,1,0,0,1,0,1,1,0,0,0,1,0,0,1,0,0,1,1,1]
    ori_spin1 = [1,0,0,0,1,0,1,1,1,1,1,1,1,1,0,0,1,1,0,0,0,0,1,0,1,0,0,1,1,0,0,1,1,1,1,0,0,1,1,0,1,1,1,1,1,1]
    sample_dict1 = {i: 1 if val == 1 else -1 for i, val in enumerate(ori_spin1)}

    H_test1 = dimod.utilities.ising_energy(sample_dict1, {}, J_dict, offset=0.0) 

    result = calculate_D_n(sample_dict1, -J)
    print(f"QB_H_test1(sample1_ori) = {H_test1}")


def calculate_D_n( s, J):
    D_all = []
    D_abssum = 0
    D_sum = 0
    for xx in range(46):
        x = 45-xx
        D_n = 0
        D_n0 = 0
        D_n1 = 0
        for y in range(23):
            J_xy = J[(x, y)]
            J_yx = J[(y, x)]
            D_n0 += J_xy * s[y]*s[x]
            D_n1 += J_yx *s[y]*s[x]
            D_n += J_xy * s[y]*s[x] + J_yx * s[y]*s[x]
        D_n2 = 0
        for y in range(23,46):
            J_xy = J[(x, y)]
            J_yx = J[(y, x)]
            D_n2 += J_xy * s[y]*s[x] + J_yx * s[y]*s[x]
        D_all.append((D_n,D_n2))
        s_str_1 = '0'
        s_str_2 = '0'
        for i in range (23):
            s_str_1 +=  str(int((s[i]+1)/2))
        for i in range(23,46):
            s_str_2 += str(int((s[i]+1)/2))
        s1_hex = hex(int(s_str_1, 2))
        s2_hex = hex(int(s_str_2, 2))
        D_subsum = D_n + D_n2
        D_sum += D_subsum
        
    return D_all

'''
def calculate_D_n( s, J):
    D_all = []
    for x in range(46):
        D_n = 0
        D_n0 = 0
        D_n1 = 0
        for y in range(23):
            J_xy = J[(x, y)]
            J_yx = J[(y, x)]
            D_n0 += J_xy * s[y]*s[x]
            D_n1 += J_yx *s[y]*s[x]
            D_n += J_xy * s[y]*s[x] + J_yx * s[y]*s[x]
        D_n2 = 0
        for y in range(23,46):
            J_xy = J[(x, y)]
            J_yx = J[(y, x)]
            D_n2 += J_xy * s[y]*s[x] + J_yx * s[y]*s[x]
        D_all.append((D_n,D_n2))
        print(f"debug parameter: Row{45-x}:{D_n0},{D_n1}")
        print(f"Row{45-x}: {D_n}, {D_n2}, {D_n+D_n2}")
    return D_all
'''
def generate_testbench(path_to_dir=None, name='test', density = 0.3):
    # path define
    rows =46
    cols =46
    if path_to_dir is None:
        path_to_dir="."
    path_to_mem_row = f"{path_to_dir}/men_row_{name}.txt"
    path_to_mem_col = f"{path_to_dir}/men_col_{name}.txt"
    path_to_matrix = f"{path_to_dir}/men_matrix_{name}.txt"
    path_to_spins = f"{path_to_dir}/men_spins_{name}.txt"
    path_to_D = f"{path_to_dir}/men_D_{name}.txt"

    # random numpy array generation
    # value_range = (-7, 7)
    value_range =(-7,7)
    num_non_zero_elements = int(rows * cols * density)
    non_zero_values = np.random.randint(value_range[0], value_range[1] + 1, num_non_zero_elements)
    matrix = np.zeros((rows, cols), dtype=int)
    indices = np.random.choice(rows * cols, num_non_zero_elements, replace=False)
    matrix.flat[indices] = non_zero_values
    np.fill_diagonal(matrix, 0)

    # solve
    J= matrix
    qbsolve = QBSolv()
    response = qbsolve.sample_ising({}, J)
    energy =response.data_vectors['energy'][0]
    # print(energy)
    reference_list = response.samples()[0]
    # save spins
    # transfer to dictionary
    J_dict = {}
    for i in range(46):
        for j in range(i):
            J_dict[(i, j)]=0
        for j in range(i,46):
            J_dict[(i,j)] = J_dict.get((i,j), 0) + J[i,j] + J[j,i]
    result = calculate_D_n(reference_list, J_dict)
    # transfer to memory row
    np.flipud(J)
    # save matrix
    num_rows, num_columns = J.shape
    memory_row = np.zeros((num_rows,num_columns)).tolist()
    for i in range(num_rows):
        for j in range(num_columns):
            memory_row[i][j] = transfer(J[i, j])

    with open(path_to_mem_row, 'w') as fp:
        for i in range(num_rows):
            for j in range(num_columns):
                fp.write(memory_row[i][j])
            fp.write('\n')


    # memory col
    np.flipud(J)
    np.transpose(J)
    np.flipud(J)
    memory_col = np.zeros((num_rows, num_columns)).tolist()
    for i in range(num_rows):
        for j in range(num_columns):
            memory_col[i][j] = transfer(J[i,j])

    with open(path_to_mem_col, 'w') as fp:
        for i in range(num_rows):
            for j in range(num_columns):
                fp.write(memory_row[i][j])
            fp.write('\n')

    result_array = np.array(result)
    np.flipud(result_array)
    D = np.sum(result_array, axis=1)

def generate_multiple_testbench(path_to_dir=None,  num=1, density = 0.3):
    for i in range(num):
        generate_testbench(path_to_dir=path_to_dir, name=i, density=density)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A random testbench generation argument parser")

    # Add command-line argument options
    parser.add_argument("-dir", "--directory", help="output_directory", type=str, default = None)
    parser.add_argument("-den", "--density", help="density", type = float, default = 0.3)
    parser.add_argument("-n","--num",  help="number of testbench to generate", type=int, default=1)
    parser.add_argument("-t","--test_mode",  action='store_true', help="test mode")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Access the parsed arguments
    dir = args.directory
    num = args.num
    density = args.density
    test_mode = args.test_mode
    if test_mode:
        test()
    else:
        if dir == None:
            if not os.path.isdir('../txt/read_verif_v1_f'):
                os.mkdir('../txt/read_verif_v1_f')
            dir = '../txt/read_verif_v1_f'

        print(f"Generating {num} ... ")
        generate_multiple_testbench(path_to_dir= dir, num=num, density=density)
        print(f"Complete")
