import os
import re
import zipfile
import tempfile
from flask import Flask, request, send_file

app = Flask(__name__)

# ---------------- AOV MAP ----------------
AOV_MAP = {
    1: '14Y',
    2: 'CPG',
    3: 'WGR',
    4: '24Y',
    5: 'RSG',
    6: 'GRG',
    7: 'GYG'
}

# ---------------- RENAME LOGIC ----------------
def transform_filename(filename):
    """
    Example input:
    G8R25CLAJRAYP611D12-TZRGL00009-Y-V1_Output AOV 3_0070.png
    """

    pattern = r"([A-Za-z0-9]+-[A-Za-z0-9]+)-([A-Za-z]+)-V(\d+)_Output AOV (\d+)_\d+\.png"
    match = re.match(pattern, filename)

    if not match:
        print("REGEX FAILED:", filename, flush=True)
        return None, None

    prefix, metal, version, aov_str = match.groups()
    aov = int(aov_str)

    wb_tb = "WB" if aov <= 7 else "TB"
    mapped_char = AOV_MAP[(aov - 1) % 7 + 1]

    final_name = f"{prefix}-{mapped_char}-V{version}-{wb_tb}.png"
    folder_name = prefix

    return final_name, folder_name


# ---------------- PROCESS DIRECTORY (RECURSIVE) ----------------
def process_directory(base_dir):
    for root, _, files in os.walk(base_dir):
        for file in files:
            if not file.lower().endswith(".png"):
                continue

            new_name, folder = transform_filename(file)
            if not new_name:
                continue

            src = os.path.join(root, file)
            dst_folder = os.path.join(root, folder)
            os.makedirs(dst_folder, exist_ok=True)

            dst = os.path.join(dst_folder, new_name)

            if os.path.exists(dst):
                print("SKIPPED (exists):", dst, flush=True)
                continue

            os.rename(src, dst)
            print("RENAMED:", src, "→", dst, flush=True)


# ---------------- UI ----------------
@app.route('/')
def index():
    return '''
    <h2>Upload Folder (PNG files)</h2>
    <form action="/process_directory" method="POST" enctype="multipart/form-data">
        <input type="file" name="files" webkitdirectory multiple required>
        <br><br>
        <button type="submit">Upload & Process</button>
    </form>
    '''


# ---------------- UPLOAD HANDLER ----------------
@app.route('/process_directory', methods=['POST'])
def process_directory_route():
    uploaded_files = request.files.getlist('files')

    if not uploaded_files:
        return "No files uploaded", 400

    with tempfile.TemporaryDirectory() as temp_dir:

        # Save uploaded folder structure
        for file in uploaded_files:
            relative_path = file.filename  # includes folder path
            save_path = os.path.join(temp_dir, relative_path)

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)

        print("UPLOAD COMPLETE", flush=True)

        # Run rename logic
        process_directory(temp_dir)

        # Zip output
        output_zip = os.path.join(temp_dir, "processed.zip")
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    if f == "processed.zip":
                        continue
                    full_path = os.path.join(root, f)
                    zipf.write(
                        full_path,
                        arcname=os.path.relpath(full_path, temp_dir)
                    )

        print("PROCESS COMPLETE", flush=True)
        return send_file(output_zip, as_attachment=True, download_name="processed.zip")


# ---------------- ENTRY ----------------
if __name__ == '__main__':
    app.run()
