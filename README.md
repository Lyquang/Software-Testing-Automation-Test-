# Python Runner Tool

Dự án này cho phép chạy **1 file Python bất kỳ** hoặc **chạy toàn bộ file trong thư mục** thông qua `main.py`.

---

## 📦 Cài đặt Dependencies

Trước khi chạy dự án, cần cài đặt các thư viện Python yêu cầu.

### 1. Cài đặt bằng `pip`
```bash
pip install -r requirements.txt
```


## 📁 Cấu trúc thư mục

```
Software-Testing-Automation-Test/
├─data/
|   ├─ customerDeposit.csv
|   ├─ customerDeposit.csv
|   ├─ manaSearchCus.csv
|   └─   ...
|
└─ scripts/
    ├─ customerDeposit.py
    ├─ customerDeposit.py
    ├─ manaSearchCus.py
    ├─ ...
    └─ main.py   ← file điều khiển chạy các script
```

## 🚀 Cách sử dụng

### 1. Di chuyển vào nơi lưu trữ các script**
```bash
    cd scripts
```

### 2. Chạy **tất cả file**
```bash
    python main.py all
```

### 3. Chạy **một file cụ thể**
```bash
    python main.py manaSearchCus.py
```

> Lưu ý: Tên file phải trùng với file trong thư mục.

---

## 📝 Nội dung `main.py` đang sử dụng

```python
import sys
import subprocess
import os

files = [f for f in os.listdir() if f.endswith(".py") and f != "main.py"]

if len(sys.argv) < 2:
    print("Sử dụng: python main.py <filename.py> | all")
    exit()

arg = sys.argv[1]

if arg == "all":
    for file in files:
        subprocess.run(["python", file])
elif arg in files:
    subprocess.run(["python", arg])
else:
    print("File không tồn tại!")
```

---

## ⚙ Yêu cầu

- Python 3.x
- Các file `.py` cần chạy nằm cùng thư mục với `main.py`

---

## Ví dụ

```bash
python main.py manaSearchCus.py      # Chạy riêng file3.py
python main.py all           # Chạy toàn bộ file
```

---

## Ghi chú

- `main.py` sẽ tự động lấy danh sách tất cả file `.py` trong thư mục (trừ chính nó).
- Nếu muốn thêm thư mục con, lọc file, hoặc chạy theo thứ tự ưu tiên, bạn có thể mở rộng code.

---

Nếu bạn cần thêm tính năng mở rộng hoặc menu chọn file, hãy yêu cầu để được hỗ trợ tiếp! 😊
