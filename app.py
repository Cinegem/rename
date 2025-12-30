import re
import os
import zipfile
import tempfile
from flask import Flask, request, send_file

app = Flask(__name__)

AOV_MAP = {
    1: '14Y', 2: 'CPG', 3: 'WGR', 4: '24Y',
    5: 'RSG', 6: 'GRG', 7: 'GYG'
}

# ---- FILENAME TRANSFORMER ----
def transform_filename(filename):
    pattern = r"([A-Za-z0-9]+-[A-Za-z0-9]+)-([A-Za-z]+)-V(\d+)_Output AOV (\d+)_\d+\.png"
    match = re.match(pattern, filename)

    if not match:
        print("Skipping unmatched file:", filename)
        return None, None

    prefix, metal, version, aov_str = match.groups()
    aov = int(aov_str)

    wb_tb = "WB" if aov <= 7 else "TB"
    mapped_char = AOV_MAP[(aov - 1) % 7 + 1]

    final_name = f"{prefix}-{mapped_char}-V{version}-{wb_tb}.png"
    folder_name = prefix

    return final_name, folder_name


# ---- PROCESS DIRECTORY ----
def process_directory(input_directory):
    for file in os.listdir(input_directory):
        if not file.lower().endswith(".png"):
            continue

        new_name, folder = transform_filename(file)
        if not new_name:
            continue

        folder_path = os.path.join(input_directory, folder)
        os.makedirs(folder_path, exist_ok=True)

        src = os.path.join(input_directory, file)
        dst = os.path.join(folder_path, new_name)

        if os.path.exists(dst):
            continue

        os.rename(src, dst)


# ---- ROUTES ----
@app.route('/')
def index():
    return '''
    <h3>Upload ZIP Folder</h3>
    <form action="/process_directory" method="POST" enctype="multipart/form-data">
        <input type="file" name="zipfile" accept=".zip" required>
        <br><br>
        <button type="submit">Upload & Process</button>
    </form>
    '''


@app.route('/process_directory', methods=['POST'])
def process_directory_route():
    uploaded_zip = request.files['zipfile']

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, "input.zip")
        uploaded_zip.save(zip_path)

        extract_dir = os.path.join(temp_dir, "input")
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        process_directory(extract_dir)

        output_zip = os.path.join(temp_dir, "processed.zip")
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(extract_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    zipf.write(
                        full_path,
                        arcname=os.path.relpath(full_path, extract_dir)
                    )

        return send_file(output_zip, as_attachment=True)


if __name__ == '__main__':
    app.run()
