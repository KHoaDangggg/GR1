import pandas as pd
import re
import os
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

        
location_list = [] # time slot + room --> avoid 2 class at same room and same time slot
lecturer_list = []
doan_nv_list = []
#Import data list giảng viên từ file
def import_lecturer():
    # Import lecturers
    # Load the Excel file
    file_path = 'data/SV.xlsx'
    excel_data = pd.read_excel(file_path, sheet_name='Phân bổ GD')
    index = 0
    # Extract data from Excel sheet and create a list of Lecturer objects
    for i, row in excel_data.iterrows():    
        expected_time_slots = row.iloc[2] * 4/3
        subjects = str(row.iloc[6])
        if subjects:
            subjects_list = re.split(r'[;,/]', subjects)
            # Remove empty strings from the list
            subjects_list = [subject.strip() for subject in subjects_list if subject.strip()]
        else:
            subjects_list = []
        if check_list_subject(subjects_list):
            continue
        if (expected_time_slots == 0) or ('nan' in subjects) or (subjects == '0'):
            continue
        lecturer = Lecturer(index, expected_time_slots, subjects_list)
        index+=1
        lecturer_list.append(lecturer)

    # Open file for writing 
    filename = 'lecturer.txt'
    with open(filename, 'w', encoding='utf-8') as f:
        for lecturer in lecturer_list:
            # Write same line to file
            line = f'ID: {lecturer.id}, Expected: {lecturer.expected_time_slots}, Subjects: {lecturer.subjects}\n'
            f.write(line.encode('utf-8').decode())
    print(f'Output written to {filename}')
    return lecturer_list

#Import data list lớp học(không tính đồ án) từ file
def import_class():
    #Import class
    excel_data = pd.read_excel('data/tkb.xlsx', sheet_name='Sheet1')
    # Extract data from Excel sheet and create a list of Lecturer objects
    class_list = []
    for index, row in excel_data.iterrows():    
        if 'TCNTT' not in row.iloc[1]:
            continue
        if 'Nhật' in row.iloc[5]:
            continue
        room_id = row.iloc[16]
        if str(room_id) == 'nan': 
            continue
        vn_name = row.iloc[5].strip()
        eng_name = row.iloc[6].strip()
        # Tạm thời bỏ qua các lớp lab do chưa clean được dữ liệu
        if 'lab'.upper() in eng_name.upper() or 'lab'.upper() in vn_name.upper():
            continue
        he_dao_tao = row.iloc[8] + row.iloc[23]
        size = convert_size(row.iloc[19])
        type_class = row.iloc[21]
        actual_time = (convert_he_dao_tao(he_dao_tao,type_class) + size) * 4/3
        start_time = convert_start_time(row.iloc[12])
        end_time = convert_end_time(row.iloc[13])
        if start_time == 0 or end_time == 0:
            continue
        thu = row.iloc[10]
        if 'S' in str(row.iloc[14]):
            kip = 0
        elif 'Ch' in str(row.iloc[14]):
            kip = 1
        start_time = int((thu - 2) * 12 + 6 * kip + start_time)
        end_time = int((thu - 2) * 12 + 6 * kip + end_time)

        for time in range(start_time, end_time+1):
            # check duplicate classroom location 
            if f'{room_id} - {time}' in location_list:
                continue
            location_list.append(f'{room_id} - {time}')
            classroom = Classroom(time, room_id, vn_name, eng_name, actual_time)
            class_list.append(classroom)
    filename = 'class.txt'
    with open(filename, 'w', encoding='utf-8') as f:
        index = 0
        for classroom in class_list:
            index+=1
            # Print to console
            # Write same line to file
            line = f'ID: {index} Time: {classroom.time_slot}, Room: {classroom.room_id}, Actual time: {classroom.actual_time},Subject: {classroom.vn_name} - {classroom.eng_name}\n'
            f.write(line.encode('utf-8').decode())
    print(f'Output written to {filename}')
    return class_list

#Import data list lớp đồ án từ file
def import_nv_do_an():
    ds_mon_doan = ['IT5024E', 'IT5030', 'IT5120E', 'IT4995', 'IT3920Q', 'IT3070Q', 'IT4995E', 'IT5005', 'IT5240Q', 'IT5315Q', 'IT3940', 'IT3150', 'IT5120', 'IT5904', 'IT4998', 'IT5023E', 'IT4940Q', 'IT3940E', 'IT3930', 'IT3910E', 'IT5022E', 'IT5030E', 'IT5021E', 'IT5022', 'IT5021', 'IT5140', 'IT5006', 'IT4993', 'IT3943']
    ds_hs_doan = {key: 0 for key in ds_mon_doan}
    file_path = 'data/SV.xlsx'
    excel_data = pd.read_excel(file_path, sheet_name='DSDA')
    list_student = []
    # Extract data from Excel sheet and create a list of Lecturer objects
    for index, row in excel_data.iterrows():    
        student = row.iloc[5]
        if student not in list_student: 
            list_student.append(student)
        else: continue
        he_dao_tao = row.iloc[10]
        doan_type = row.iloc[1]
        mon_hoc = row.iloc[1]
        ds_hs_doan[mon_hoc]+=1
        actual_time = convert_doan(he_dao_tao) * convert_doan_type(doan_type) * 4/3
        doan = DoAn(mon_hoc, student, actual_time)
        doan_nv_list.append(doan)
    
    return ds_hs_doan

#Xử lí dât cho các môn (không tính đồ án)
#Xử lí time slot cho các lớp 
def convert_start_time(time):
    if time == 645 or time == 1230:
        return 1
    if time == 825  or time == 1410:
        return 2
    if time == 920 or time == 1505 or time == 1500:
        return 3
    if time == 1015 or time == 1600:
        return 4
    if time in range(1,6):
        return time
    return 0

def convert_end_time(time):
    if time == 815  or time == 1400:
        return 2
    if time == 910 or time == 915 or time == 1455:
        return 3
    if time == 1005 or time == 1550:
        return 4
    if time == 1100 or time == 1645:
        return 5
    if time == 1145 or time == 1730:
        return 6
    if time in range(2,7):
        return time
    return 0

#Convert hệ số theo hệ đào tạo
def convert_he_dao_tao(he_dao_tao, type_class):
    if 'LT' in type_class:
        if 'ELICTECH' in he_dao_tao:
            if 'Nhật' in he_dao_tao or 'Pháp' in he_dao_tao or 'Tài năng'in he_dao_tao:
                return 1.8
            else: return 2
        else: return 1.5
    else:
        if 'ELITECH' in he_dao_tao:
            return 1.5
        else: return 1

#Convert hệ số theo size lớp 
def convert_size(size):
    if size in range(0,61):
        return 0
    if size in range(61,121):
        return 0.2
    if size in range(121,181):
        return 0.4
    if size in range(181,241):
        return 0.6
    if size in range(241,301):
        return 0.8
    if size in range(301,1000):
        return 1

#Conevert cho các môn dồ án
#Convert hệ số theo hệ đào tạo cho môn đồ án  
def convert_doan(doan_type):
    if 'CTTT' in doan_type:
        return 0.2
    if 'SIE' in doan_type or 'HESDPI' in doan_type or 'KSTN' in doan_type or 'Phap' in doan_type:
        return 0.18
    else: return 0.12

#Convert hệ số theo số tín chỉ môn hồ án
def convert_doan_type(doan):
    if doan in ['IT5315Q','IT5240Q','IT5904']:
        return 12
    if doan in ['IT4995E','IT4995']:
        return 6
    if doan in ['IT5120','IT5140','IT5120E']:
        return 9
    if doan in ['IT3930','IT5021','IT3150','IT5023E','IT5030','IT5022','IT5024E','IT3910E',]:
        return 2
    if doan in ['IT4998','IT4993',]:
        return 8
    if doan in ['IT3070Q','IT5006','IT5022E','IT5005','IT3940','IT3940E','IT3943','IT5030E','IT5021E','IT4940Q','IT3920Q']:
        return 3
    
def check_list_subject(subjects_list):
    if 'Tin học đại cương' in subjects_list or 'Introduction to Computer Science' in subjects_list:
        return False
    if 'Introduction to ICT' in subjects_list or 'Nhập môn CNTT và TT' in subjects_list:
        return False
    if 'Technical Writing and Presentation' in subjects_list:
        return False
    if 'Cấu trúc dữ liệu và giải thuật' in subjects_list or 'Data Structures and Algorithms' in subjects_list:
        return False
    if 'Cấu trúc dữ liệu và thuật toán' in subjects_list:
        return False
    if 'Cấu trúc dữ liệu và GT' in subjects_list:
        return False
    if 'Toán rời rạc' in subjects_list or 'Discrete Mathematics' in subjects_list:
        return False
    return True


# cac mon do an




def import_data():
    import_lecturer()
    class_list = import_class()
    ds_hs_doan = import_nv_do_an()

    for index in range(0,len(doan_nv_list)):
        doan = doan_nv_list[index]
        doan.nv1 = lecturer_list[index%56].id
        doan.nv2 = lecturer_list[(index+1)%56].id
        doan.nv3 = lecturer_list[(index+2)%56].id


    # Open file for writing 
    filename = 'doan.txt'
    with open(filename, 'w', encoding='utf-8') as f:
        index = 0
        for doan in doan_nv_list:
            index+=1
            # Write same line to file
            line = f'id: {index}Loai do an: {doan.mon_hoc}, Student: {doan.student}, actual_time: {doan.actual_time}, nv1: {doan.nv1}, nv2: {doan.nv2}, nv3: {doan.nv3} \n'
            f.write(line.encode('utf-8').decode())
    print(f'Output written to {filename}')
    return lecturer_list, doan_nv_list, class_list, ds_hs_doan