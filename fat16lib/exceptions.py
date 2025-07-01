class FAT16Error(Exception):
    """Base exception for FAT16 operations"""
    pass

class NotEnoughSpaceError(FAT16Error):
    """Raised when there's not enough space for an operation"""
    pass

class FileNotFoundError(FAT16Error):
    """Raised when a file is not found"""
    pass

class InvalidFileNameError(FAT16Error):
    """Raised when a file name is invalid"""
    pass

class InvalidDiskImageError(FAT16Error):
    """Raised when a disk Image is invalid"""
    pass

class FileAccessError(FAT16Error):
    """Raised when a file access is invalid"""
    pass