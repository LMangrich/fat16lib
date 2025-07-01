# FAT16 Library

A Python library for reading and manipulating FAT16 filesystem images, developed as part of an Operating Systems course project.
It certainly has a lot of issues and it was built with a bunch of tears and frustration but it works!

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

# Initialize with disk image (supports absolute/relative paths)
fat = FAT16('disk.img')  # or r'C:\path\to\disk.img'

# 1. List files
for filename, size in fat.list_files():
    print(f"{filename} ({size} bytes)")

# 2. Read file (text or binary)
try:
    # For text files:
    content = fat.read_file('README.TXT')
    print(content)

    # For binary files:
    image_data = fat.read_file('IMAGE.BMP')
except FileNotFoundError as e:
    print(f"Error: {e}")

# 3. File operations
fat.rename_file('OLD.TXT', 'NEW.TXT')  # Rename
fat.delete_file('TRASH.TXT')           # Delete
fat.insert_external_file('NEWFILE.TXT') # Add from host system

# 4. Get metadata
attrs = fat.get_file_attributes('CONFIG.TXT')
print(f"Created at: {attrs['date_created']}")
```

## API Reference

### FAT16 Class

```
__init__(image_path)
```

Initialize with path to FAT16 image file.

#### Methods:

- list_files(): Returns list of (filename, size) tuples

- read_file(filename): Returns file content as string (or bytes for binary files)

- get_file_attributes(filename): Returns dictionary with file attributes

- rename_file(old_name, new_name): Renames a file

- delete_file(filename): Deletes a file

- insert_external_file(external_path): Inserts external file into image

#### Exceptions

- FAT16Error: Base exception class

- FileNotFoundError: Raised when file doesn't exist

- NotEnoughSpaceError: Raised when no space for operation

- InvalidFileNameError: Raised for invalid FAT16 filenames

- InvalidDiskImageError: Raised for invalid FAT16 disk image

- FileAccessError: Raised when file access is denied

## Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.
But I may warn you, it's been ages since my last deep dive into FAT16, so I might need to study it a bit again!

## License

This project is licensed under the MIT License - see the [LICENSE file](https://github.com/LMangrich/fat16lib/blob/main/LICENSE) for details.
