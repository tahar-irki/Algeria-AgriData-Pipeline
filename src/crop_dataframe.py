import kagglehub
import shutil
import os


PROJECT_ROOT = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )


DATA_DIR = os.path.join(PROJECT_ROOT, "data")


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