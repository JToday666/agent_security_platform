import json
import os

# Path to the input JSON file
input_path = "sample_bbc.json"  # Replace with your path if different
output_dir = "test_cases_webplatform2"   # Folder to store output files
os.makedirs(output_dir, exist_ok=True)

# Load the input JSON
with open(input_path, "r") as f:
    data = json.load(f)

# Iterate through each test case and write to a separate file
for item in data:
    if "URLxxx" in item['user_prompt']:
        item['user_prompt'] = item['user_prompt'].replace("URLxxx", item['url'])
    filename = f"{item['id']}.json"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w") as out_file:
        json.dump(item, out_file, indent=4)

print(f"Split {len(data)} test cases into '{output_dir}/'")
