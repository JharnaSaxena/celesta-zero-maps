import os
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_ZIP = BASE_DIR / "terrascope-jezero-carter.zip"

EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".idea",
    ".vscode"
}

EXCLUDE_EXTS = {
    ".pyc",
    ".pyo"
}

def create_archive():
    count = 0
    total_bytes = 0
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                file_path = Path(root) / file
                # Skip the zip file itself and excluded file extensions
                if file_path == OUTPUT_ZIP:
                    continue
                if file_path.suffix in EXCLUDE_EXTS:
                    continue

                rel_path = file_path.relative_to(BASE_DIR)
                zipf.write(file_path, arcname=str(rel_path).replace("\\", "/"))
                count += 1
                total_bytes += file_path.stat().st_size

    size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"Archive created successfully!")
    print(f"Path:  {OUTPUT_ZIP}")
    print(f"Files: {count}")
    print(f"Size:  {size_mb:.2f} MB")

if __name__ == "__main__":
    create_archive()
