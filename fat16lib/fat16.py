import datetime
import os
import struct
from .constants import *
from .utils import *
from .exceptions import *

class FAT16:
    def __init__(self, image_path):
        """Initialize FAT16 filesystem handler with disk image path"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Disk image not found: {image_path}")
        self.image_path = image_path

    def read_boot_sector(self, img_file):
        """Read and parse FAT16 boot sector information"""
        try:
            boot_sector = img_file.read(512)

            bytes_per_sector = struct.unpack_from("<H", boot_sector, BYTES_PER_SECTOR_OFFSET)[0]
            sectors_per_cluster = struct.unpack_from("<B", boot_sector, SECTORS_PER_CLUSTER_OFFSET)[0]
            reserved_sectors = struct.unpack_from("<H", boot_sector, RESERVED_SECTORS_OFFSET)[0]
            number_of_fats = struct.unpack_from("<B", boot_sector, NUMBER_OF_FATS_OFFSET)[0]
            root_dir_entries = struct.unpack_from("<H", boot_sector, ROOT_DIR_ENTRIES_OFFSET)[0]
            sectors_per_fat = struct.unpack_from("<H", boot_sector, SECTORS_PER_FAT_OFFSET)[0]

            root_dir_start = (reserved_sectors + (number_of_fats * sectors_per_fat)) * bytes_per_sector

            return bytes_per_sector, sectors_per_fat, number_of_fats, root_dir_entries, reserved_sectors, sectors_per_cluster, root_dir_start
        except struct.error as e:
            raise InvalidDiskImageError(f"Invalid boot sector structure: {str(e)}")

    def read_disk_data(self, img_file, bytes_per_sector, reserved_sectors, sectors_per_fat, number_of_fats, root_dir_entries):
        """Read root directory data from disk"""
        root_dir_start = bytes_per_sector * (reserved_sectors + sectors_per_fat * number_of_fats)
        root_dir_size = root_dir_entries * DIR_ENTRY_SIZE

        img_file.seek(root_dir_start)
        root_dir_data = img_file.read(root_dir_size)

        return root_dir_size, root_dir_data

    def list_files(self):
        """List all files in root directory"""
        with open(self.image_path, 'rb') as img_file:
            bytes_per_sector, sectors_per_fat, number_of_fats, root_dir_entries, reserved_sectors, sectors_per_cluster, root_dir_start = self.read_boot_sector(img_file)
            root_dir_size, root_dir_data = self.read_disk_data(img_file, bytes_per_sector, reserved_sectors, sectors_per_fat, number_of_fats, root_dir_entries)

            files = [] 

            for i in range(0, root_dir_size, DIR_ENTRY_SIZE):
                entry = root_dir_data[i:i + DIR_ENTRY_SIZE]
                if entry[0] == ENTRY_FREE:
                    break
                if entry[0] == ENTRY_DELETED:
                    continue

                file_name = entry[0:FILE_NAME_SIZE].decode('ascii').strip()
                file_extension = entry[FILE_NAME_SIZE:FILE_NAME_SIZE+FILE_EXT_SIZE].decode('ascii').strip()
                full_name = f"{file_name}.{file_extension}" if file_extension else file_name

                file_size_bytes = entry[28:32] 
                file_size = int.from_bytes(file_size_bytes, byteorder='little')

                files.append((full_name, file_size))

        return files

    def read_file(self, file):
        """Read complete content of specified file"""
        try:
            with open(self.image_path, 'rb') as img_file:
                bytes_per_sector, sectors_per_fat, number_of_fats, root_dir_entries, reserved_sectors, sectors_per_cluster, root_dir_start = self.read_boot_sector(img_file)
                root_dir_size, root_dir_data = self.read_disk_data(img_file, bytes_per_sector, reserved_sectors, sectors_per_fat, number_of_fats, root_dir_entries)

                content = None

                for i in range(0, root_dir_size, DIR_ENTRY_SIZE):
                    entry = root_dir_data[i:i + DIR_ENTRY_SIZE]
                    if entry[0] == ENTRY_FREE:
                        break
                    if entry[0] == ENTRY_DELETED:
                        continue

                    file_name = entry[0:FILE_NAME_SIZE].decode('ascii').strip()
                    file_extension = entry[FILE_NAME_SIZE:FILE_NAME_SIZE+FILE_EXT_SIZE].decode('ascii').strip()
                    full_name = f"{file_name}.{file_extension}" if file_extension else file_name

                    if full_name == file:
                        first_cluster = struct.unpack_from("<H", entry, 26)[0]
                        file_size_bytes = entry[28:32] 
                        file_size = int.from_bytes(file_size_bytes, byteorder='little')
                        
                        first_data_sector = reserved_sectors + number_of_fats * sectors_per_fat + (root_dir_entries * DIR_ENTRY_SIZE + bytes_per_sector - 1) // bytes_per_sector
                        file_content_start = (first_data_sector + (first_cluster - 2) * sectors_per_cluster) * bytes_per_sector

                        img_file.seek(file_content_start)
                        content = img_file.read(file_size)
                        break

            if content is None:
                raise FileNotFoundError(f"File '{file}' not found")
            try:
                return content.decode('latin-1')
            except UnicodeDecodeError:
                return content
        except (IOError, struct.error) as e:
            raise FileAccessError(f"Error reading file: {str(e)}")

    def get_file_attributes(self, file):
        """Get attributes and metadata for specified file"""
        try:
            with open(self.image_path, 'rb') as img_file:
                bytes_per_sector, sectors_per_fat, number_of_fats, root_dir_entries, reserved_sectors, sectors_per_cluster, root_dir_start = self.read_boot_sector(img_file)
                root_dir_size, root_dir_data = self.read_disk_data(img_file, bytes_per_sector, reserved_sectors, sectors_per_fat, number_of_fats, root_dir_entries)
            
            for i in range(0, root_dir_size, DIR_ENTRY_SIZE):
                    entry = root_dir_data[i:i + DIR_ENTRY_SIZE]
                    if entry[0] == ENTRY_FREE:
                        break
                    if entry[0] == ENTRY_DELETED:
                        continue

                    file_name = entry[0:FILE_NAME_SIZE].decode('ascii').strip()
                    file_extension = entry[FILE_NAME_SIZE:FILE_NAME_SIZE+FILE_EXT_SIZE].decode('ascii').strip()
                    full_name = f"{file_name}.{file_extension}" if file_extension else file_name

                    if full_name == file:
                        file_attribute_byte = entry[11]
                        file_attribute = int(file_attribute_byte)

                        file_time_created_byte = entry[22:24]
                        file_time = decode_time(file_time_created_byte)

                        file_date_created_byte = entry[24:26]
                        file_date = decode_date(file_date_created_byte)

                        is_read_only = bool(file_attribute & READ_ONLY)
                        is_hidden = bool(file_attribute & HIDDEN)
                        is_system = bool(file_attribute & SYSTEM)

                        return {
                            "file_name": file,
                            "read_only": is_read_only,
                            "hidden": is_hidden,
                            "system": is_system,
                            "time_created": file_time,
                            "date_created": file_date
                        }
            
            raise FileNotFoundError(f"File '{file}' not found")
        except IOError as e:
            raise FileAccessError(f"Could not access disk image: {str(e)}")    
    
    def rename_file(self, file, new_file_name): 
        """Rename a file in the filesystem"""
        with open(self.image_path, 'r+b') as img_file:
            bytes_per_sector, sectors_per_fat, number_of_fats, root_dir_entries, reserved_sectors, sectors_per_cluster, root_dir_start = self.read_boot_sector(img_file)
            root_dir_size, root_dir_data = self.read_disk_data(img_file, bytes_per_sector, reserved_sectors, sectors_per_fat, number_of_fats, root_dir_entries)

            name_part, ext_part = split_filename(new_file_name)
            if not name_part:
                raise InvalidFileNameError("Invalid file name")

            new_file_name_bytes = name_part.ljust(FILE_NAME_SIZE).encode('ascii') + ext_part.ljust(FILE_EXT_SIZE).encode('ascii')

            for i in range(0, root_dir_size, DIR_ENTRY_SIZE):
                entry = root_dir_data[i:i + DIR_ENTRY_SIZE]
                if entry[0] == ENTRY_FREE:
                    break
                if entry[0] == ENTRY_DELETED:
                    continue
                
                file_name = entry[0:FILE_NAME_SIZE].decode('ascii').strip()
                file_extension = entry[FILE_NAME_SIZE:FILE_NAME_SIZE+FILE_EXT_SIZE].decode('ascii').strip()
                full_name = f"{file_name}.{file_extension}" if file_extension else file_name

                if full_name == file:
                    file_position = root_dir_start + i 
                    img_file.seek(file_position)
                    img_file.write(new_file_name_bytes)
                    return True

        return False

    def find_free_clusters(self, img_file, num_clusters, fat_start, fat_size):
        """Find contiguous free clusters in FAT"""
        img_file.seek(fat_start)
        fat = img_file.read(fat_size)

        free_clusters = []
        for i in range(2, len(fat) // 2):
            if struct.unpack_from('<H', fat, i * 2)[0] == 0x0000:
                free_clusters.append(i)
                if len(free_clusters) == num_clusters:
                    break
        return free_clusters

    def update_fat(self, img_file, clusters, fat_start):
        """Update FAT with cluster chain"""
        for i in range(len(clusters) - 1):
            img_file.seek(fat_start + clusters[i] * 2)
            img_file.write(struct.pack('<H', clusters[i + 1]))

        img_file.seek(fat_start + clusters[-1] * 2)
        img_file.write(struct.pack('<H', END_OF_CLUSTER))

    def write_file_content(self, img_file, content, clusters, data_start, bytes_per_sector, sectors_per_cluster):
        """Write file content to allocated clusters"""
        cluster_size = bytes_per_sector * sectors_per_cluster
        for i, cluster in enumerate(clusters):
            file_path = data_start + (cluster - 2) * cluster_size
            img_file.seek(file_path)
            img_file.write(content[i * cluster_size: (i + 1) * cluster_size])

    def insert_external_file(self, external_file_path):
        """Insert external file into FAT16 filesystem"""
        if not os.path.exists(external_file_path):
            raise FileNotFoundError(f"Source file not found: {external_file_path}")
        
        try: 
            with open(external_file_path, 'rb') as external_file:
                file_content = external_file.read()
            file_size = len(file_content)
        except IOError as e:
            raise FileAccessError(f"Could not read source file: {str(e)}")

        try:
            with open(self.image_path, 'r+b') as img_file:
                bytes_per_sector, sectors_per_fat, number_of_fats, root_dir_entries, reserved_sectors, sectors_per_cluster, root_dir_start = self.read_boot_sector(img_file)
                root_dir_size, root_dir_data = self.read_disk_data(img_file, bytes_per_sector, reserved_sectors, sectors_per_fat, number_of_fats, root_dir_entries)

                fat_start = reserved_sectors * bytes_per_sector
                fat_size = sectors_per_fat * bytes_per_sector
                data_start = root_dir_start + root_dir_entries * DIR_ENTRY_SIZE

                clusters_needed = (file_size + bytes_per_sector * sectors_per_cluster - 1) // (bytes_per_sector * sectors_per_cluster)
                clusters = self.find_free_clusters(img_file, clusters_needed, fat_start, fat_size)

                if len(clusters) < clusters_needed:
                    raise NotEnoughSpaceError("There are not enough free clusters")

                attributes = get_attributes(external_file_path)
                file_metadata = os.stat(external_file_path)

                time_creation = file_metadata.st_ctime
                creation_date = datetime.datetime.fromtimestamp(time_creation)

                time_created = (creation_date.hour * 3600 + creation_date.minute * 60 + creation_date.second) // 2
                year = creation_date.year - 1980
                month = creation_date.month
                day = creation_date.day
                date_created = (year << 9) | (month << 5) | day

                entry_found = False
                for i in range(0, root_dir_size, DIR_ENTRY_SIZE):
                    entry = root_dir_data[i:i + DIR_ENTRY_SIZE]

                    if entry[0] == ENTRY_FREE or entry[0] == ENTRY_DELETED:
                        file_position = root_dir_start + i
                        img_file.seek(file_position)

                        name, ext = os.path.basename(external_file_path).rsplit('.', 1)
                        name_part, ext_part = split_filename(f"{name}.{ext}")

                        entry_data = bytearray(DIR_ENTRY_SIZE)
                        entry_data[0:FILE_NAME_SIZE] = name_part.ljust(FILE_NAME_SIZE).encode('ascii')
                        entry_data[FILE_NAME_SIZE:FILE_NAME_SIZE+FILE_EXT_SIZE] = ext_part.ljust(FILE_EXT_SIZE).encode('ascii')
                        entry_data[11] = attributes
                        entry_data[22:24] = encode_time(time_created)
                        entry_data[24:26] = encode_date(date_created)
                        entry_data[26:28] = struct.pack('<H', clusters[0])
                        entry_data[28:32] = struct.pack('<I', file_size)
                        
                        img_file.write(entry_data)
                        entry_found = True
                        break
                
                if not entry_found:
                    raise NotEnoughSpaceError("There are no available directory entries")
                
                self.update_fat(img_file, clusters, fat_start)
                self.write_file_content(img_file, file_content, clusters, data_start, bytes_per_sector, sectors_per_cluster)
        except IOError as e:
            raise FileAccessError(f"Could not access disk image: {str(e)}")


    def delete_file(self, file): 
        """Delete file from filesystem and free allocated clusters"""
        try:
            with open(self.image_path, 'r+b') as img_file:
                bytes_per_sector, sectors_per_fat, number_of_fats, root_dir_entries, reserved_sectors, sectors_per_cluster, root_dir_start = self.read_boot_sector(img_file)
                root_dir_size, root_dir_data = self.read_disk_data(img_file, bytes_per_sector, reserved_sectors, sectors_per_fat, number_of_fats, root_dir_entries)

                first_data_sector = reserved_sectors + number_of_fats * sectors_per_fat + (root_dir_entries * DIR_ENTRY_SIZE + bytes_per_sector - 1) // bytes_per_sector

                for i in range(0, root_dir_size, DIR_ENTRY_SIZE):
                    entry = root_dir_data[i:i + DIR_ENTRY_SIZE]
                    if entry[0] == ENTRY_FREE:
                        break
                    if entry[0] == ENTRY_DELETED:
                        continue
                    
                    file_name = entry[0:FILE_NAME_SIZE].decode('ascii').strip()
                    file_extension = entry[FILE_NAME_SIZE:FILE_NAME_SIZE+FILE_EXT_SIZE].decode('ascii').strip()
                    full_name = f"{file_name}.{file_extension}" if file_extension else file_name

                    if full_name == file:
                        file_position = root_dir_start + i 
                        try:
                            img_file.seek(file_position)
                            first_cluster = struct.unpack_from("<H", entry, 26)[0]
                            img_file.write(bytes([ENTRY_DELETED] + [0] * (DIR_ENTRY_SIZE - 1)))

                            fat_start = reserved_sectors * bytes_per_sector
                            
                            current_cluster = first_cluster
                            clusters_to_clear = []

                            while current_cluster < END_OF_CLUSTER:
                                clusters_to_clear.append(current_cluster)

                                img_file.seek(fat_start + current_cluster * 2)
                                next_cluster = struct.unpack_from('<H', img_file.read(2))[0]

                                if next_cluster >= END_OF_CLUSTER:
                                    break

                                current_cluster = next_cluster

                            for cluster in clusters_to_clear:
                                cluster_offset = (first_data_sector + (cluster - 2) * sectors_per_cluster) * bytes_per_sector
                                img_file.seek(cluster_offset)
                                img_file.write(b'\x00' * (sectors_per_cluster * bytes_per_sector))
                                
                                img_file.seek(fat_start + cluster * 2)
                                img_file.write(struct.pack('<H', 0x0000))
                            
                            return True
                        except IOError as e:
                            raise FileAccessError(f"Delete operation failed: {str(e)}")
            return False
        except IOError as e:
            raise FileAccessError(f"Could not access disk image: {str(e)}")