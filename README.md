#Project GR1 - 2023.1
#SV: Đặng Phúc Khoa - mssv: 20210486
GVHD: TS. Vũ Thị Hương Giang

Mục đích: Cài đặt và chạy thử nghiệm thuật toán Simulated Annealing, Integer Linear Programming, Tabu Search cho bài toán phân công lịch giảng dạy cho giảng viên trường đại học

Cấu trúc: 
-	Folder data: chứa các file excel về data các lớp học, nguyện vọng đồ án của sinh viên, giảng viên
-	Data: gồm 1582 nguyện vọng đồ án, 87 giảng viên, 1267 lớp học
o	Class.txt: Lưu thông tin về các tiết học. Một lớp học gồm nhiều tiết học sẽ được chia thành nhiều lớp học. Thông tin một lớp học gồm: ID(unique), Time_slot, Room, Actual_time (Số giờ thực dạy trong mỗi tiết học), Eng_name, Vn_name
o	Lecturer.txt: Lưu thông tin các giảng viên gồm: ID(unique), Expected(Số giờ làm việc mong muốn / 1 tuần), Subjects (các môn thuộc chuyên môn)
o	Doan.txt: Lưu thông tin các nguyện vọng đồ án gồm: Loại đồ án, Student, actual_time (số giờ hướng dẫn thực tế / 1 tuần), nv1, nv2, nv3 (tương ứng với giáo viên theo 3 nguyện vọng)
- File utils.py: viết các hàm kiểm tra ràng buộc, hàm đánh giá lời giải, in lời giải
- File data.py: viết các hàm import data từ file excel, xử lí Data
- File integer_programming.py: chứa thuật toán ILP
- File tabu_search: chứa thuật toán tabu Search
- File simulated_annealing.py: chứa thuật toán Simulated Annealing

HƯỚNG DẪN CHẠY:
Các thuật toán được chạy thử nghiêm với 3 bộ dữ liệu. Code đang chọn mặc định chạy thử nghiệm thuật toán trên bộ dữ liệu 3

+ Chạy thuật toán ILP: python .\integer_programming.py
+ Chạy thuật toán tabu Search: python .\tabu_search.py
+ Chạy thuật toán Simulated Annealing: python .\simulated_annealing.py
