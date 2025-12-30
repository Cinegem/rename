import re
import os
import subprocess
from flask import Flask, request

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

    # WB or TB logic
    wb_tb = "WB" if aov <= 7 else "TB"

    # Looping AOV mapping 1–7 for 8–14
    mapped_char = AOV_MAP[(aov - 1) % 7 + 1]

    # Final output file name
    final_name = f"{prefix}-{mapped_char}-V{version}-{wb_tb}.png"

    # Folder name
    folder_name = prefix

    return final_name, folder_name




# ---- PROCESS DIRECTORY ----
def process_directory(input_directory):

    # -------------------------
    # STEP 1 — RENAME FILES
    # -------------------------
    for file in os.listdir(input_directory):
        if not file.endswith(".png"):
            continue

        new_name, folder = transform_filename(file)
        if not new_name:
            continue

        folder_path = os.path.join(input_directory, folder)
        os.makedirs(folder_path, exist_ok=True)

        src = os.path.join(input_directory, file)
        dst = os.path.join(folder_path, new_name)

        if os.path.exists(dst):
            print("Already exists, skipping:", dst)
            continue

        os.rename(src, dst)
        print("Renamed:", file, "→", dst)

    # -------------------------


@app.route('/')
def index():
    return '''
    <form action="/process_directory" method="POST">
        <input type="text" name="input_dir" placeholder="Directory Path" required>
        <button type="submit">Process</button>
    </form>
    '''

@app.route('/process_directory', methods=['POST'])
def process_directory_route():
    input_dir = request.form['input_dir']
    print("Directory received:", input_dir)
    process_directory(input_dir)
    return "Done processing " + input_dir


if __name__ == '__main__':
    app.run(debug=True)
