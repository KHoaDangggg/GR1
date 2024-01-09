from ortools.linear_solver import pywraplp
import utils
import data
import time
import math

time_start = time.perf_counter()

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




#Import data từ file excel
lecturers, nv_doans, classrooms, ds_hs_do_an = data.import_data()
  
# data 1
# nv_doans = nv_doans[:400]
# classrooms = classrooms[:100]
# lecturers = lecturers[:]

#data 2
# nv_doans = nv_doans[:800]
# classrooms = classrooms[:200]
# lecturers = lecturers

#data 3
nv_doans = nv_doans[:]
classrooms = classrooms[:420]
lecturers = lecturers

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
        if lecturer.id == doan.nv1 or lecturer.id == doan.nv2 or lecturer == doan.nv3:
            continue
        total_assigned +=doan_assignments[(lecturer.id, doan.student, doan.mon_hoc, doan.actual_time, doan.nv1, doan.nv2, doan.nv3)]
    solver.Add(total_assigned == 0)

# Một giảng viên chỉ được hướng dẫn tối đa 3 học sinh có cùng môn đồ án
for lecturer in lecturers:
    for mon_do_an in ds_hs_do_an.keys():
        total_assigned = 0
        for doan in nv_doans:
            if doan.mon_hoc != mon_do_an: 
                continue
            total_assigned+=doan_assignments[(lecturer.id, doan.student, doan.mon_hoc, doan.actual_time, doan.nv1, doan.nv2, doan.nv3)]
        solver.Add(total_assigned <= math.ceil(ds_hs_do_an[mon_do_an] * 1.5 / 56))

# Each classroom should be assigned to exactly one lecturer
for classroom in classrooms:
    total_assigned = sum(assignments[(lecturer.id, classroom.time_slot, classroom.room_id, classroom.vn_name,classroom.actual_time)] for lecturer in lecturers)
    solver.Add(total_assigned == 1) 

# Difference between actual and expected working hours of lecturers must be <= max_allowed_difference
for lecturer in lecturers:
    total_assigned_hours = 0
    total_assigned_hours+=sum(assignments[(lecturer.id, classroom.time_slot, classroom.room_id, classroom.vn_name, classroom.actual_time)] * classroom.actual_time for classroom in classrooms)
    total_assigned_hours+=sum(doan_assignments[(lecturer.id, doan.student, doan.mon_hoc, doan.actual_time, doan.nv1, doan.nv2, doan.nv3)] * doan.actual_time for doan in nv_doans)
    max_allowed_difference = lecturer.expected_time_slots * 0.6
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

# 1 giảng viên dạy >=min_class, <=max_class giờ cho các tiết học trên lớp
# Set min_class và mã_class
min_class = 10 # data1: 0 data2: 0 data3: 10
max_class = 30 # data1: 20 data2: 19 data3: 25
for lecturer in lecturers:
    total_assigned_hours = 0
    total_assigned_hours+=sum(assignments[(lecturer.id, classroom.time_slot, classroom.room_id, classroom.vn_name, classroom.actual_time)] * classroom.actual_time for classroom in classrooms)
    solver.Add(total_assigned_hours >= min_class)
    solver.Add(total_assigned_hours <= max_class)

# 1 giảng viên dạy >=min_class, <=max_class giờ cho các tiết hướng dẫn đồ án
# Set min_class và mã_class
min_doan = 15 # data1: 3 data2: 6 data3: 15
max_doan = 20 # data1: 5 data2: 14 data3: 20
for lecturer in lecturers:
    total_assigned_doan_hours = 0
    total_assigned_doan_hours+=sum(doan_assignments[(lecturer.id, doan.student, doan.mon_hoc, doan.actual_time, doan.nv1, doan.nv2, doan.nv3)] * doan.actual_time for doan in nv_doans)
    solver.Add(total_assigned_doan_hours >= min_doan)
    solver.Add(total_assigned_doan_hours <= max_doan)

# min < Số giờ dạy / số giờ hướng dẫn < max của 1 giảng viên
for lecturer in lecturers:
    total_doan_assigned_hours = 0
    total_doan_assigned_hours+=sum(doan_assignments[(lecturer.id, doan.student, doan.mon_hoc, doan.actual_time, doan.nv1, doan.nv2, doan.nv3)] * doan.actual_time for doan in nv_doans)
    total_assigned_hours = 0
    total_assigned_hours+=sum(assignments[(lecturer.id, classroom.time_slot, classroom.room_id, classroom.vn_name,classroom.actual_time)] * classroom.actual_time for classroom in classrooms)
    solver.Add(total_assigned_hours >=( total_doan_assigned_hours * 0.6))
    solver.Add(total_assigned_hours <=( total_doan_assigned_hours * 1.4))




# Objective
# Minimize total extra class
exceeding_expected = {}
for lecturer in lecturers:
    exceeding_expected[lecturer.id] = solver.IntVar(0, 70, f'exceeding_{lecturer.id}')
for lecturer in lecturers:
    total_assigned_hours = 0
    total_assigned_hours+=sum(assignments[(lecturer.id, classroom.time_slot, classroom.room_id, classroom.vn_name, classroom.actual_time)] * classroom.actual_time for classroom in classrooms)
    total_assigned_hours+=sum(doan_assignments[(lecturer.id, doan.student, doan.mon_hoc, doan.actual_time, doan.nv1, doan.nv2, doan.nv3)] * doan.actual_time for doan in nv_doans)
    solver.Add(total_assigned_hours <= lecturer.expected_time_slots + exceeding_expected[lecturer.id])
total_exceeding_teachers = solver.Sum(exceeding_expected.values())
solver.Minimize(total_exceeding_teachers)

#Phân công giáo viên với nguyện vọng cao nhất cho học sinh
doan_assign_nv = 0
for doan in nv_doans:
    for lecturer in lecturers:
        if doan_assignments[(lecturer.id, doan.student, doan.mon_hoc, doan.actual_time, doan.nv1, doan.nv2, doan.nv3)]:
            if lecturer.id == doan.nv1: doan_assign_nv+=1
            if lecturer.id == doan.nv2: doan_assign_nv+=2
            if lecturer.id == doan.nv3: doan_assign_nv+=3
solver.Minimize(doan_assign_nv)

#Tối thiểu số lượng giáo viên dạy ít giờ hơn dự kiến
below_expected = {}
for lecturer in lecturers:
    below_expected[lecturer.id] = solver.IntVar(0, 70, f'below_{lecturer.id}')
for lecturer in lecturers:
    total_assigned_hours = 0
    total_assigned_hours+=sum(assignments[(lecturer.id, classroom.time_slot, classroom.room_id, classroom.vn_name, classroom.actual_time)] * classroom.actual_time for classroom in classrooms)
    total_assigned_hours+=sum(doan_assignments[(lecturer.id, doan.student, doan.mon_hoc, doan.actual_time, doan.nv1, doan.nv2, doan.nv3)] * doan.actual_time for doan in nv_doans)
    solver.Add(total_assigned_hours >= lecturer.expected_time_slots - below_expected[lecturer.id])
total_below_teachers = solver.Sum(below_expected.values())

# solver.Minimize(total_below_teachers * 0.2 + total_exceeding_teachers * 0.2 + doan_assign_nv * 0.001)


# Solve the problem
solver.Solve()

time_end = time.perf_counter()

result_assignments = {}
result_doans = {}
# Iterate through the assignments dictionary and extract solution values
for key, variable in assignments.items():
    lecturer_id, time_slot, room_id, vn_name, actual_time = key
    result_assignments[(lecturer_id, time_slot, room_id, vn_name, actual_time)] = variable.solution_value()

for key, variable in doan_assignments.items():
    lecturer_id, student, mon_hoc, actual_time, nv1, nv2, nv3 = key
    result_doans[(lecturer_id, student, mon_hoc, actual_time, nv1, nv2, nv3)] = variable.solution_value()
# Print the solution table
for lec in lecturers:   
    utils.find_classes_for_lecturer(lec.id, result_assignments,result_doans)

print(f'Executin time: {time_end - time_start: .6f} seconds to run')
print(f'Cost for solution: {utils.evaluate_cost(result_assignments, result_doans, lecturers)}')