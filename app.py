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
    pattern = r"([A-Za-z0-9]+-[A-Za-z0-9]+)-([A-Za-z]+)-V(\d+)_Output AOV (\d+)_\d+\.png"
    match = re.match(pattern, filename)

    if not match:
        print("SKIPPED (regex fail):", filename, flush=True)
        return None, None

    prefix, metal, version, aov_str = match.groups()
    aov = int(aov_str)

    wb_tb = "WB" if aov <= 7 else "TB"
    mapped_char = AOV_MAP[(aov - 1) % 7 + 1]

    final_name = f"{prefix}-{mapped_char}-V{version}-{wb_tb}.png"
    folder_name = prefix

    return final_name, folder_name


# ---------------- PROCESS FILES ----------------
def process_files(upload_dir, processed_dir):
    for root, _, files in os.walk(upload_dir):
        for file in files:
            if not file.lower().endswith(".png"):
                continue

            new_name, folder = transform_filename(file)
            if not new_name:
                continue  # ❌ HARD SKIP FAILED FILES

            src = os.path.join(root, file)
            dst_folder = os.path.join(processed_dir, folder)
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
    <h2>Upload Folder (PNG only)</h2>
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
        upload_dir = os.path.join(temp_dir, "upload")
        processed_dir = os.path.join(temp_dir, "processed")

        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)

        # Save uploaded folder structure
        for file in uploaded_files:
            save_path = os.path.join(upload_dir, file.filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)

        print("UPLOAD COMPLETE", flush=True)

        # Process ONLY valid files
        process_files(upload_dir, processed_dir)

        # Zip ONLY processed files
        output_zip = os.path.join(temp_dir, "processed.zip")
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(processed_dir):
                for f in files:
                    full_path = os.path.join(root, f)
                    zipf.write(
                        full_path,
                        arcname=os.path.relpath(full_path, processed_dir)
                    )

        print("PROCESS COMPLETE (CLEAN OUTPUT)", flush=True)
        return send_file(output_zip, as_attachment=True, download_name="processed.zip")


# ---------------- ENTRY ----------------
if __name__ == '__main__':
    app.run()
