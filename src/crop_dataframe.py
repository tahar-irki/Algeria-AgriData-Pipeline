import kagglehub
import shutil
import os




def find_data_dir(start_path):
    curr = os.path.abspath(start_path)
    while curr != os.path.dirname(curr):
        # Check if a directory named 'data' exists in the current level
        potential_data_path = os.path.join(curr, 'data')
        if os.path.isdir(potential_data_path):
            return potential_data_path
        curr = os.path.dirname(curr)
    return None

# Get the dynamic path
DATA_DIR = find_data_dir(__file__)



tmp_path = kagglehub.dataset_download(
    "miadul/precision-agriculture-crop-selection-dataset"
)

os.makedirs(DATA_DIR, exist_ok=True)


for file_name in os.listdir(tmp_path):
    source = os.path.join(tmp_path, file_name)
    destination = os.path.join(DATA_DIR, file_name)

    if os.path.exists(destination):
        os.remove(destination)

    shutil.move(source, destination)
    print(f"Moved: {file_name}")

print(f"\nSuccess! Files are now in: {DATA_DIR}")