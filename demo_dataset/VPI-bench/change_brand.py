import os
import json

# Thư mục chứa các file JSON gốc
input_folder = "./webplatform"       # ← Thư mục chứa file gốc
output_folder = "./webplatform2"      # ← Thư mục lưu file mới

# Danh sách các cặp old → new cần thay thế
replace_map = {
    "amazon": "bbc",
    "Before going shopping": "Before reading news",
    "Welcome to Shopping Mall!!": "Welcome !"
}

os.makedirs(output_folder, exist_ok=True)

def recursive_replace(obj):
    if isinstance(obj, dict):
        return {recursive_replace(k): recursive_replace(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [recursive_replace(elem) for elem in obj]
    elif isinstance(obj, str):
        new_str = obj
        for old, new in replace_map.items():
            new_str = new_str.replace(old, new)
        return new_str
    else:
        return obj

def replace_in_filename(name: str) -> str:
    new_name = name
    for old, new in replace_map.items():
        new_name = new_name.replace(old, new)
    return new_name

# Duyệt tất cả file JSON trong thư mục
for filename in os.listdir(input_folder):
    if filename.endswith(".json"):
        input_path = os.path.join(input_folder, filename)

        # Đọc nội dung JSON
        with open(input_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"❌ Lỗi đọc JSON: {filename}")
                continue

        # Thay thế nội dung
        updated_data = recursive_replace(data)

        # Đổi tên file nếu có chứa keyword
        new_filename = replace_in_filename(filename)
        output_path = os.path.join(output_folder, new_filename)

        # Ghi file mới
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Đã tạo: {new_filename}")
