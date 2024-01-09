from ortools.linear_solver import pywraplp
import utils
import data
import time
import math
import copy
import random

#Define model
class Classroom:
    def __init__(self, time_slot, room_id, vn_name, eng_name, actual_time):
        self.time_slot = time_slot
        self.room_id = room_id
        self.actual_time = actual_time
        self.vn_name = vn_name
        self.eng_name = eng_name
class Lecturer:
    def __init__(self, id, expected_time_slots, subjects):
        self.id = id
        self.expected_time_slots = expected_time_slots
        self.subjects = subjects
        self.list_doan = []
class DoAn:
    def __init__(self, mon_hoc, student, actual_time):
        self.mon_hoc = mon_hoc
        self.student = student
        self.actual_time = actual_time

# Result assignments: 
result_assignments = {}
result_doans = {}

#Import data từ file excel
lecturers, nv_doans, classrooms, ds_hs_do_an = data.import_data()

def intialize_solution():
    # Create a Solver instance
    solver = pywraplp.Solver.CreateSolver('CBC') 

    # Define decision variables
    assignments = {}
    for lecturer in lecturers:
        for classroom in classrooms:
            assignments[(lecturer.id, classroom.time_slot, classroom.room_id, classroom.vn_name, classroom.actual_time)] = solver.BoolVar(f'x_{lecturer.id}_{classroom.time_slot}_{classroom.room_id}_{classroom.vn_name}_{classroom.actual_time}')

    doan_assignments = {}
    for doan in nv_doans:
        for lecturer in lecturers:
            doan_assignments[(lecturer.id, doan.student, doan.mon_hoc, doan.actual_time, doan.nv1, doan.nv2, doan.nv3)] = solver.BoolVar(f'x_{lecturer.id}_{doan.student}_{doan.mon_hoc}_{doan.actual_time}_{doan.nv1}_{doan.nv2}_{doan.nv3}')


    # Constraints
    # Các đồ án đều được chỉ định 1 giáo viên hướng dẫn
    for doan in nv_doans:
        total_assigned = sum(doan_assignments[(lecturer.id, doan.student, doan.mon_hoc, doan.actual_time, doan.nv1, doan.nv2, doan.nv3)] for lecturer in lecturers)
        solver.Add(total_assigned == 1)

    #đồ án được hướng dẫn bởi 1 trong 3 giáo viên trong 3 nguyện vọng
    for doan in nv_doans:
        total_assigned = 0
        for lecturer in lecturers:
            if lecturer.id == doan.nv1 or lecturer.id == doan.nv2 or lecturer.id == doan.nv3:
                continue
            total_assigned +=doan_assignments[(lecturer.id, doan.student, doan.mon_hoc, doan.actual_time, doan.nv1, doan.nv2, doan.nv3)]
        solver.Add(total_assigned == 0)


    # Each classroom should be assigned to exactly one lecturer
    for classroom in classrooms:
        total_assigned = sum(assignments[(lecturer.id, classroom.time_slot, classroom.room_id, classroom.vn_name, classroom.actual_time)] for lecturer in lecturers)
        solver.Add(total_assigned == 1) 

    # Difference between actual and expected working hours of lecturers must be <= 70%
    for lecturer in lecturers:
        total_assigned_hours = 0
        total_assigned_hours+=sum(assignments[(lecturer.id, classroom.time_slot, classroom.room_id, classroom.vn_name, classroom.actual_time)] * classroom.actual_time for classroom in classrooms)
        total_assigned_hours+=sum(doan_assignments[(lecturer.id, doan.student, doan.mon_hoc, doan.actual_time, doan.nv1, doan.nv2, doan.nv3)] * doan.actual_time for doan in nv_doans)
        max_allowed_difference = lecturer.expected_time_slots * 1.5
        solver.Add(total_assigned_hours  >= lecturer.expected_time_slots - max_allowed_difference)
        solver.Add(total_assigned_hours  <= lecturer.expected_time_slots + max_allowed_difference)

    # Lecturers can only teach <= 1 class at 1 time slot
    for lecturer in lecturers:
        for time_slot in range(1, 84):  # Assuming 12 x 7 time slots
            total_assigned_classes = 0    
            for classroom in classrooms:
                if ((lecturer.id, time_slot, classroom.room_id, classroom.vn_name, classroom.actual_time) in assignments) and classroom.time_slot == time_slot:
                    total_assigned_classes+=assignments[(lecturer.id, time_slot, classroom.room_id, classroom.vn_name, classroom.actual_time)]
            solver.Add(total_assigned_classes <= 1) 

    # Lecturers can only teach subjects they are major in
    for lecturer in lecturers:
        for classroom in classrooms:
            check = True
            for sub in lecturer.subjects:
                if classroom.vn_name in sub or classroom.eng_name in sub :
                    check = False
                    break
            if check:
                solver.Add(assignments[(lecturer.id, classroom.time_slot, classroom.room_id, classroom.vn_name, classroom.actual_time)] == 0)
    # Solve the problem
    solver.Solve()
    # Iterate through the assignments dictionary and extract solution values
    for key, variable in assignments.items():
        lecturer_id, time_slot, room_id, vn_name, actual_time = key
        result_assignments[(lecturer_id, time_slot, room_id, vn_name, actual_time)] = variable.solution_value()

    for key, variable in doan_assignments.items():
        lecturer_id, student, mon_hoc, actual_time, nv1, nv2, nv3 = key
        result_doans[(lecturer_id, student, mon_hoc, actual_time, nv1, nv2, nv3)] = variable.solution_value()

def mutate_ideal_doan_assignment(result_assignments, result_doans, lecturers):
    ## Chỉ định 1 giáo viên có chuyên môn phù hợp để hướng dẫn thay 1 đồ án. Thực hiện với 1/4 số nguyện vọng đồ án (chọn ngẫu nhiên)
    condition = True
    mutate_doan_assignment = copy.deepcopy(result_doans)
    class_lec, doan_lec, total_hour_lec = utils.get_total_hour_lecturer(result_assignments, result_doans, lecturers)
    count = 5
    # List chứa các class nên đưọc thay đổi trong lời giải mói
    # Thay lớp đồ án có giáo viên đang dạy quá giờ
    # Thay lớp đồ án có giáo viên đang có hệ số class / đồ án < 57/43
    assigned_lec_doan = []
    for key, value in mutate_doan_assignment.items():
        if total_hour_lec[key[0]] > 0.45 * lecturers[key[0]].expected_time_slots:
            continue
        if value == 1 and key[0] != key[4]:
            assigned_lec_doan.append(key)
    # Số nguyện vọng thay đổi trong 1 lần
    select_num = 5
    while(condition and count > 0):
        condition = False
        if len(assigned_lec_doan) > select_num:
            random_selection = random.sample(assigned_lec_doan, select_num)
        else: random_selection = assigned_lec_doan
        for (l_id, student, mon_hoc, time, nv1, nv2, nv3) in random_selection:
            mutate_doan_assignment[(l_id, student, mon_hoc, time, nv1, nv2, nv3)] = 0
            if total_hour_lec[nv1] < 0.65 * lecturers[nv1].expected_time_slots:
                mutate_doan_assignment[(nv1, student, mon_hoc, time, nv1, nv2, nv3)] = 1
            elif total_hour_lec[nv1] < 0.65 * lecturers[nv1].expected_time_slots:
                mutate_doan_assignment[(nv2, student, mon_hoc, time, nv1, nv2, nv3)] = 1
            else:
                count-=1
                condition = True
                break

    
    return mutate_doan_assignment

def mutate_ideal_class_assignment(result_assignments, doan_assignments, lecturers):
    condition = True
    # Chỉ định 1 giáo viên có chuyên môn phù hợp để dạy thay 1 lớp bất kì. Thực hiện với 1/4 số lớp học (chọn ngẫu nhiên)
    mutate_class_assignment = copy.deepcopy(result_assignments)
    class_lec, doan_lec, total_hour_lec = utils.get_total_hour_lecturer(result_assignments, doan_assignments, lecturers)

    # List chứa các class nên đưuọc thay đổi trong lời giải mói
    # Thay lớp có giáo viên đang dạy quá giờ
    # Thay lớp có giáo biên đang có hệ số class / đồ án > 57/43
    assigned_lec_class = []
    for key, value in mutate_class_assignment.items():
        if value == 1 and total_hour_lec[key[0]] > lecturers[key[0]].expected_time_slots * 0.5:
            assigned_lec_class.append(key)
    count = 5

    while(condition and count > 0):
        #print(len(assigned_lec_class))
        (lecturer_id, time_slot, room_id, vn_name, actual_time) = random.choice(assigned_lec_class)

        for lec in lecturers:
            if vn_name in lec.subjects and total_hour_lec[lec.id]<lecturers[lec.id].expected_time_slots*0.5:
                mutate_class_assignment[(lecturer_id, time_slot, room_id, vn_name, actual_time)] = 0
                mutate_class_assignment[(lec.id, time_slot, room_id, vn_name, actual_time)] = 1
                break
        
        condition = not (utils.check_hard_constraints_class(mutate_class_assignment, lecturers, classrooms))
        count-=1
    return mutate_class_assignment

def simulated_annealing(result_assignments, result_doans, lecturers):
    print('Evaluate initial assignment: ')
    print(utils.evaluate_cost(result_assignments, result_doans, lecturers))
    # number of iterations
    iter_count = 50

    # cost cho Lời giải ban đầu
    cur_cost = utils.evaluate_cost(result_assignments, result_doans, lecturers)['total_cost']
    print(cur_cost)
    tabu_list = []
    for i in range(iter_count):

        # Thay đổi lời giải
        mutate_class_assignment = copy.deepcopy(mutate_ideal_class_assignment(result_assignments, result_doans, lecturers))
        mutate_doan_assignment = copy.deepcopy(mutate_ideal_doan_assignment(result_assignments, result_doans, lecturers))
        # Đánh giá lời giải mới
        new_cost = utils.evaluate_cost(mutate_class_assignment, mutate_doan_assignment, lecturers)
        lec_values = utils.convert_assign_lecture_to_value(mutate_class_assignment)
        doan_values = utils.convert_assign_doan_to_value(mutate_doan_assignment)
        # Bỏ qua nếu lời giải mới đã nằm trong tabu list
        if lec_values in tabu_list:
            continue
        if doan_values in tabu_list:
            continue
        # Loại bỏ phần tử khi tabu list đầy
        if len(tabu_list) == 20:
            tabu_list.pop()
            tabu_list.pop()
        tabu_list.append(lec_values)
        tabu_list.append(doan_values)
        if new_cost['total_cost'] < cur_cost:
            result_assignments = copy.deepcopy(mutate_class_assignment)
            result_doans = copy.deepcopy(mutate_doan_assignment)
            cur_cost = new_cost['total_cost']
            print(new_cost)
        
    #print result
    print('Evaluate assignment after simulated annealing: ')
    print(utils.evaluate_cost(result_assignments, result_doans, lecturers))

# data 1
# nv_doans = nv_doans[:400]
# classrooms = classrooms[:100]
# lecturers = lecturers[:]

#data 2
# nv_doans = nv_doans[:800]
# classrooms = classrooms[:200]
# lecturers = lecturers

# #data 3
nv_doans = nv_doans[:]
classrooms = classrooms[:420]
lecturers = lecturers

def main():
    time_start = time.perf_counter()
    
    intialize_solution()
    if utils.check_hard_constraint_doan(result_doans, nv_doans):
        print('check initial solution')
    simulated_annealing(result_assignments, result_doans, lecturers)

    # Print the solution table
    # for lec in lecturers:   
    #     utils.find_classes_for_lecturer(lec.id, result_assignments,result_doans)

    time_end = time.perf_counter()
    print(f'Executin time: {time_end - time_start: .6f} seconds to run')


main()