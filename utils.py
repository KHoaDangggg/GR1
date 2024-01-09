def find_classes_for_lecturer(lecturer_id, assignments, nv_doan):
    print(f'Classes for Lecturer {lecturer_id}:')
    total_class = 0
    total_doan = 0
    for (l_id, time_slot, room_id, subject_id, actual_time), variable in assignments.items():
        if l_id == lecturer_id and variable == 1:
            #print(f'Time Slot {time_slot} - Room {room_id} - Subject {subject_id}')
            total_class+=actual_time

    for (l_id, student, mon_hoc, time, nv1, nv2, nv3), variable in nv_doan.items():
        if l_id == lecturer_id and variable == 1:
            total_doan+=float(time)
            #print(f'Student: {student} - Mon hoc: {mon_hoc}')

    print(f'Total assignement: {total_class} - Total doan: {total_doan}')

def evaluate_cost(class_assignment, doan_assignment, lecturers):
    result = {}
    result['lecturer_exceed_cost'] = 0
    result['lecturer_below_cost'] = 0
    result['doan_cost'] = 0
    total_hour_lecturer = {}
    result['total_empty_cost']  = 0# tổng số giờ trống giữa các tiết cùng ngày của giáo viên 
    result['avg_hour_dif'] = 0

    # Tính chênh lệch số giờ dạy trung bình so vói kì vọng của giáo viên và số giáo viên dạy thiếu giờ, quá số giờ dự kiến 
    for lec in lecturers:
        total = 0
        for (l_id, time_slot, room_id, subject_id, actual_time), variable in class_assignment.items():
            if lec.id == l_id and variable == 1:
                total+=actual_time
        total_hour_lecturer[lec.id] = total

    lectures_doan = {}
    for lec in lecturers:
        lectures_doan[lec.id] = 0
    # Tính độ thỏa mãn theo ưu tiên nguyện vọng của học sinh
    for (l_id, student, mon_hoc, time, nv1, nv2, nv3), variable in doan_assignment.items():
        if variable == 0:
            continue
        if l_id == nv1:
            result['doan_cost']+=1
        elif l_id == nv2:
            result['doan_cost']+=2
        elif l_id == nv3:
            result['doan_cost']+=3
        lectures_doan[l_id] += time
    
    total_avg_hour_dif = 0
    for lec in lecturers:
        if total_hour_lecturer[lec.id] + lectures_doan[lec.id]  < lec.expected_time_slots * 0.5:
            result['lecturer_below_cost']+=1
        if total_hour_lecturer[lec.id] + lectures_doan[lec.id] > lec.expected_time_slots * 0.5:
            result['lecturer_exceed_cost']+=1
        total_avg_hour_dif += abs((total_hour_lecturer[lec.id] + lectures_doan[lec.id] - lec.expected_time_slots)/lec.expected_time_slots)
        
    result['avg_hour_diff'] = total_avg_hour_dif/len(lecturers)   

    # Tính tỉ lệ trung bình giữa giờ giảng dạy và giờ hướng dẫn của giáo viên
    avg_ratio_lec_doan = 0 
    for lec in lecturers:
        if(lectures_doan[lec.id]) == 0:
            continue
        avg_ratio_lec_doan += total_hour_lecturer[lec.id]/lectures_doan[lec.id]
    
    result['avg_ratio_cost'] = avg_ratio_lec_doan/len(lecturers);

    

    # Tính tổng số giờ trống giữa các giờ trống trong cùng ngày của giáo viên
    time_slots = {}
    for (l_id, time_slot, room_id, subject_id, actual_time), variable in class_assignment.items():
        if variable == 0: continue
        if l_id not in time_slots:
            time_slots[l_id] = [time_slot]
            continue
        time_slots[l_id].append(time_slot)
    for id, time_slot in time_slots.items():  
        time_slot.sort()
        # print(id)
        # print(time_slot)
        for i in range(0, len(time_slot)-1):
            if time_slot[i]%12 != time_slot[i+1]%12:
                continue
            result['total_empty_cost'] += abs(time_slot[i+1] - time_slot[i] - 1)


    result['total_cost'] = result['lecturer_exceed_cost'] * 0.2 + result['lecturer_below_cost'] * 0.2 + result['doan_cost'] * 0.001 +  result['total_empty_cost'] * 0.01 + abs(result['avg_ratio_cost'] - 57/43) * 0.05 + result['avg_hour_diff'] * 0.1

    return result

def check_hard_constraints_class(class_assignment, lecturers, classes):
    # Check cac lop hoc deu duoc chi dinh 1 giao vien
    for lop in classes:
        total = 0
        for (l_id, time_slot, room_id, subject_id, actual_time), variable in class_assignment.items():
            if time_slot == lop.time_slot and room_id == lop.room_id:
                total+=variable
        if total != 1:
            return False
        
    # Check 1 giao vien day <= 1 tiet trong 1 time slot
    for lec in lecturers:
        time_slots = []
        for (l_id, time_slot, room_id, subject_id, actual_time), variable in class_assignment.items():
            if lec.id == l_id and variable == 1:
                time_slots.append(time_slot)
        if len(time_slots) != len(set(time_slots)):
            return False
        
    # Check giao vien chi day cac lop trong linh vuc chuyen mon
    for lec in lecturers:
        for (l_id, time_slot, room_id, subject_id, actual_time), variable in class_assignment.items():
            if lec.id == l_id and variable == 1 and subject_id not in lec.subjects:
                return False

    return True   

def check_hard_constraint_doan(doan_assignment, doans):
    # Check do an chi duoc assign cho 1 trong 3 giao vien trong nguyen vong
    for doan in doans:
        total = 0
        for (l_id, student, mon_hoc, time, nv1, nv2, nv3), variable in doan_assignment.items():
            if l_id != nv1 and l_id != nv2 and l_id != nv3 and variable == 1:
                return False
            if student == doan.student:
                total+=variable
        if total != 1:
            return False
    
    return True
    # for i in range(0,56):
    #     total = 0
    #     for (l_id, student, mon_hoc, time, nv1, nv2, nv3), variable in doan_assignment.items():
    #         if student == doans[i].student and variable == 1:
    #             # print(l_id, student, mon_hoc, time, nv1, nv2, nv3)
    #             total+=1
    #     print(total)

def get_total_hour_lecturer(class_assignment, doan_assignment, lecturers):
    hour_lec = {}
    doan_lec = {}
    class_lec = {}
    for lec in lecturers:
        hour_lec[lec.id] = 0
        doan_lec[lec.id] = 0
        class_lec[lec.id] = 0
    for (l_id, time_slot, room_id, subject_id, actual_time), variable in class_assignment.items():
        if variable == 1:
            hour_lec[l_id]+=actual_time
            class_lec[l_id]+=actual_time
    for (l_id, student, mon_hoc, time, nv1, nv2, nv3), variable in doan_assignment.items():
        if variable == 1:
            hour_lec[l_id]+=time
            doan_lec[l_id]+=time
    return class_lec, doan_lec, hour_lec    


def convert_assign_lecture_to_value(class_assignment):
    values = {0}
    for (l_id, time_slot, room_id, subject_id, actual_time), variable in class_assignment.items():
        if variable == 0:
            continue
        values.add(str(l_id) + ":" + str(time_slot) + " at " + str(room_id))
    return values

def convert_assign_doan_to_value(doan_assignment):
    values = {0}
    for (l_id, student, mon_hoc, time, nv1, nv2, nv3), variable in doan_assignment.items():
        if variable == 1:
            continue
        values.add(str(l_id) + "teach" + str(student))
    return values
 



    




          
          
