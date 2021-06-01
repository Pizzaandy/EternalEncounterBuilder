import ctypes
import os
import shutil
from pathlib import Path
from io import BytesIO
from sys import platform


def is_binary(filename):
    try:
        with open(filename, "tr") as check_file:  # try open file in text mode
            check_file.read()
            return False
    except ValueError:  # if fail then file is non-text (binary)
        return True


def decompress_entities(filename, dest_filename="") -> bool:
    """
    Decompress a .entities file
    Requires oo2core_8_win64.dll (windows) or liblinoodle.so (linux)
    to be in the folder
    :param filename:
    :param dest_filename:
    :return:
    """
    if not is_binary(filename):
        print("File is already decompressed")
        if dest_filename:
            shutil.copy(filename, dest_filename)
        return False

    dest_filename = filename if not dest_filename else dest_filename

    with open(filename, "rb") as file:
        file_data = file.read()

    with BytesIO(file_data) as bio:
        bio.seek(0x0)
        uncompressed_size = int.from_bytes(bio.read(8), "little")
        bio.seek(0x8)
        compressed_size = int.from_bytes(bio.read(8), "little")
        bio.seek(0x10)
        bytes_data = bio.read()
        if len(bytes_data) != compressed_size:
            raise ValueError(
                f"File size is {len(bytes_data)}, expected {compressed_size}. Bad file!"
            )

    compressed_buf = ctypes.create_string_buffer(bytes_data)
    compressed_data = ctypes.cast(compressed_buf, ctypes.POINTER(ctypes.c_ubyte))

    decompressed_buf = ctypes.create_string_buffer(uncompressed_size)
    decompressed_data = ctypes.cast(decompressed_buf, ctypes.POINTER(ctypes.c_ubyte))

    if "linux" in platform:
        oodle_path = "./liblinoodle.so"
    else:
        oodle_path = "./oo2core_8_win64.dll"

    try:
        oodlz_decompress = ctypes.cdll[oodle_path]["OodleLZ_Compress"]
    except OSError:
        raise FileNotFoundError(f"{oodle_path[2:]} not in folder!")

    oodlz_decompress.restype = ctypes.c_int
    oodlz_decompress.argtypes = [
        ctypes.POINTER(ctypes.c_ubyte),  # src_buf
        ctypes.c_int,  # src_len
        ctypes.POINTER(ctypes.c_ubyte),  # dst
        ctypes.c_size_t,  # dst_size
        ctypes.c_int,  # fuzz
        ctypes.c_int,  # crc
        ctypes.c_int,  # verbose
        ctypes.POINTER(ctypes.c_ubyte),  # dst_base
        ctypes.c_size_t,  # e
        ctypes.c_void_p,  # cb
        ctypes.c_void_p,  # cb_ctx
        ctypes.c_void_p,  # scratch
        ctypes.c_size_t,  # scratch_size
        ctypes.c_int,  # threadPhase
    ]

    if (
        ret := oodlz_decompress(
            compressed_data,
            compressed_size,
            decompressed_data,
            ctypes.c_size_t(uncompressed_size),
            1,
            1,
            0,
            None,
            0,
            None,
            None,
            None,
            0,
            0,
        )
        != uncompressed_size
    ):
        print(f"expected size of {uncompressed_size}, got '{ret}' :(")
        return True

    with open(dest_filename, "w") as file:
        file.write(ctypes.string_at(decompressed_buf).decode())

    if dest_filename:
        print(f"Decompressed {Path(filename).name} to {Path(dest_filename).name}")
    else:
        print(f"Decompressed {Path(filename).name}")
    return False


def compress_entities(filename, dest_filename="") -> bool:
    """
    Compress a .entities file
    Requires oo2core_8_win64.dll (windows) or liblinoodle.so (linux)
    to be in the folder
    :param filename:
    :param dest_filename:
    :return:
    """
    if is_binary(filename):
        print("File is already compressed")
        if dest_filename:
            shutil.copy(filename, dest_filename)
        return False

    dest_filename = filename if not dest_filename else dest_filename

    size = os.path.getsize(filename)

    with open(filename, "rb") as file:
        decompressed_buf = ctypes.create_string_buffer(file.read(), size)
    decompressed_data = ctypes.cast(decompressed_buf, ctypes.POINTER(ctypes.c_ubyte))

    try:
        compressed_buf = ctypes.create_string_buffer(size + 65536)  # magic number?
    except MemoryError:
        raise MemoryError("Couldn't allocate memory for compression")
    compressed_data = ctypes.cast(compressed_buf, ctypes.POINTER(ctypes.c_ubyte))

    if "linux" in platform:
        oodle_path = "./liblinoodle.so"
    else:
        oodle_path = "./oo2core_8_win64.dll"

    try:
        oodlz_compress = ctypes.cdll[oodle_path]["OodleLZ_Compress"]
    except OSError:
        raise FileNotFoundError(f"{oodle_path[2:]} not in folder!")

    oodlz_compress.restype = ctypes.c_int
    oodlz_compress.argtypes = [
        ctypes.c_int,  # codec
        ctypes.POINTER(ctypes.c_ubyte),  # src_buf
        ctypes.c_size_t,  # src_len
        ctypes.POINTER(ctypes.c_ubyte),  # dst
        ctypes.c_int,  # level
        ctypes.c_void_p,  # opts
        ctypes.c_size_t,  # offs
        ctypes.c_size_t,  # unused
        ctypes.c_void_p,  # scratch
        ctypes.c_size_t,  # scratch_size
    ]

    compressed_size = oodlz_compress(
        13, decompressed_data, ctypes.c_size_t(size), compressed_data, 4, 0, 0, 0, 0, 0
    )

    if compressed_size < 0:
        print(f"{compressed_size} is negative, compression failed!")
        return True

    with open(dest_filename, "wb") as file:
        file.write(size.to_bytes(8, "little"))
        file.write(compressed_size.to_bytes(8, "little"))
        file.write(compressed_buf[0:compressed_size])

    if dest_filename:
        print(f"Compressed {Path(filename).name} to {Path(dest_filename).name}")
    else:
        print(f"Compressed {Path(filename).name}")

    return False
