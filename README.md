# FAT16 Library

A Python library for reading and manipulating FAT16 filesystem images, developed as part of an Operating Systems course project.
It certainly has a lot of issues, but it was built with plenty of tears and frustration!

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/fat16lib.svg)](https://pypi.org/project/fat16lib/)

## Features

- List files in FAT16 image
- Read file contents
- View file attributes (read-only, hidden, system)
- Rename files
- Delete files
- Insert external files into the image
- Supports both file and directory operations

## Installation

You can install the library using pip:

```bash
pip install fat16lib
```

Or directly from source:

```
git clone https://github.com/Lmangrich/Fat16lib.git
cd fat16lib
pip install .
```

## Usage

### Basic Usage

```
from fat16lib import FAT16

# Open a FAT16 image file
fat = FAT16('disk_image.img')

# List all files
files = fat.list_files()
for name, size in files:
    print(f"{name} ({size} bytes)")

# Read a file
try:
    content = fat.read_file('README.TXT')
    print(content)
except FileNotFoundError as e:
    print(f"Error: {e}")

# Get file attributes
attrs = fat.get_file_attributes('README.TXT')
print(f"Attributes: {attrs}")

# Rename a file
fat.rename_file('OLDNAME.TXT', 'NEWNAME.TXT')

# Delete a file
fat.delete_file('TO_DELETE.TXT')

# Insert an external file
fat.insert_file('/path/to/local/file.txt', 'NEWFILE.TXT')
```

### Advanced Usage

```
# Check for errors
try:
    fat.delete_file('NONEXISTENT.TXT')
except FileNotFoundError as e:
    print(f"Operation failed: {e}")

# Working with binary files
binary_data = fat.read_file('IMAGE.BMP')  # Returns bytes for non-text files
```

## API Reference

### FAT16 Class

```
__init__(image_path)
```

Initialize with path to FAT16 image file.

#### Methods:

list_files(): Returns list of (filename, size) tuples

read_file(filename): Returns file content as string (or bytes for binary files)

get_file_attributes(filename): Returns dictionary with file attributes

rename_file(old_name, new_name): Renames a file

delete_file(filename): Deletes a file

insert_file(external_path, target_name=None): Inserts external file into image

#### Exceptions

FAT16Error: Base exception class

FileNotFoundError: Raised when file doesn't exist

NotEnoughSpaceError: Raised when no space for operation

InvalidFileNameError: Raised for invalid FAT16 filenames

## Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
