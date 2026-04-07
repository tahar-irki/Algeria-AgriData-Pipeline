import kagglehub
import shutil
import os
tmp_path = kagglehub.dataset_download("shankarpriya2913/crop-and-soil-dataset")
current_dir = os.getcwd()
files = os.listdir(tmp_path)
for file_name in files:
    source = os.path.join(tmp_path, file_name)
    destination = os.path.join(current_dir, file_name)
    shutil.move(source, destination)
    print(f"Moved: {file_name}")

print("\nSuccess! Files are now in your root folder.")