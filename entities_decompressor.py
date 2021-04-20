import subprocess
from pathlib import Path

fp1 = r'C:\_DEV\EternalEncounterDesigner\Test Entities\e3m2_hell.entities'
fp2 = r'C:\_DEV\EternalEncounterDesigner\Test Entities\funny_test.entities'
fp3 = r'C:\_DEV\EternalEncounterDesigner\Test Entities\test.entities'

def decompress_entities(input_path, output_path, exe="idFileDeCompressor.exe"):
    if not Path(exe).exists():
        print("ERROR: idFileDeCompressor not in folder!")
        return None
    subprocess.run(['idFileDeCompressor.exe',"-d",input_path, output_path])

def compress_entities(input_path, output_path, exe="idFileDeCompressor.exe"):
    if not Path(exe).exists():
        print("ERROR: idFileDeCompressor not in folder!")
        return None
    subprocess.run(['idFileDeCompressor.exe',"-c",input_path, output_path])


decompress_entities(fp2, fp3)
