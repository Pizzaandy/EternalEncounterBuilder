from pathlib import Path
import shutil
import subprocess


def is_binary(filename):
    try:
        with open(filename, 'tr') as check_file:  # try to open file in text mode
            check_file.read()
            return False
    except:  # if fail, then file is non-text (binary)
        return True


def decompress(input_path, output_path="", exe="idFileDeCompressor.exe"):
    new_path = True
    if not Path(exe).exists():
        print("ERROR: idFileDeCompressor not in folder!")
        return False
    if Path(input_path).suffix != ".entities":
        print("ERROR: Input path is not an .entities file!")
        return False
    if not is_binary(input_path):
        print("File is already decompressed!")
        if output_path:
            shutil.copy(input_path, output_path)
        return True
    if not output_path:
        new_path = False
        output_path = input_path
    p = subprocess.run(['idFileDeCompressor.exe',"-d", input_path, output_path])
    if p.stderr:
        print(f"STINKY: {p.stderr}")
        return False
    if new_path:
        print(f"Decompressed {Path(input_path).name} to {Path(output_path).name}")
    else:
        print(f"Decompressed {Path(input_path).name}")
    return True

def compress(input_path, output_path="", exe="idFileDeCompressor.exe"):
    new_path = True
    if not Path(exe).exists():
        print("ERROR: idFileDeCompressor not in folder!")
        return None
    if Path(input_path).suffix != ".entities":
        print("ERROR: Input path is not an .entities file!")
        return False
    if is_binary(input_path):
        print("File is already compressed!")
        if output_path:
            shutil.copy(input_path, output_path)
        return True
    if not output_path:
        new_path = False
        output_path = input_path
    p = subprocess.run(['idFileDeCompressor.exe',"-c", input_path, output_path])
    if p.stderr:
        print(f"ERROR: {p.stderr}")
        return False
    if new_path:
        print(f"Compressed {Path(input_path).name} to {Path(output_path).name}")
    else:
        print(f"Compressed {Path(input_path).name}")
    return True


