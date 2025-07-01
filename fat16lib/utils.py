import struct
import os
import stat
from .constants import *

def decode_time(time_bytes):
    """Decode FAT16 time format"""
    time = int.from_bytes(time_bytes, byteorder='little')
    hours = (time >> 11) & 0x1F
    minutes = (time >> 5) & 0x3F
    seconds = (time & 0x1F) * 2
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def decode_date(date_bytes):
    """Decode FAT16 date format"""
    date = int.from_bytes(date_bytes, byteorder='little')
    year = ((date >> 9) & 0x7F) + 1980
    month = (date >> 5) & 0x0F
    day = date & 0x1F
    return f"{year:04}-{month:02}-{day:02}"

def encode_time(dt):
    """Encode datetime to FAT16 time format"""
    time = (dt.hour << 11) | (dt.minute << 5) | (dt.second // 2)
    return struct.pack('<H', time)

def encode_date(dt):
    """Encode datetime to FAT16 date format"""
    year = dt.year - 1980
    date = (year << 9) | (dt.month << 5) | dt.day
    return struct.pack('<H', date)

def get_attributes(external_file):
    """Get file attributes from external file"""
    attributes = 0
    file_stats = os.stat(external_file)
    file_attributes = file_stats.st_file_attributes

    if file_attributes & stat.FILE_ATTRIBUTE_READONLY:
        attributes |= READ_ONLY
    if file_attributes & stat.FILE_ATTRIBUTE_HIDDEN:
        attributes |= HIDDEN
    if file_attributes & stat.FILE_ATTRIBUTE_SYSTEM:
        attributes |= SYSTEM

    return attributes

def split_filename(filename):
    """Split filename into 8.3 format"""
    if '.' in filename:
        name, ext = filename.split('.', 1)
        name = name[:FILE_NAME_SIZE].upper()
        ext = ext[:FILE_EXT_SIZE].upper()
    else:
        name = filename[:FILE_NAME_SIZE].upper()
        ext = ''
    return name, ext