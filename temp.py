import os

def delete_files_not_ending_in_zero(folder_path):
    # Iterate through all files in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        # Check if it's a file and does not end in '0'
        if os.path.isfile(file_path) and not filename.endswith('_0.jpg'):
            try:
                os.remove(file_path)
                print(f"Deleted: {filename}")
            except Exception as e:
                print(f"Error deleting {filename}: {e}")

# Example usage:
# folder_path = "path/to/your/folder"
delete_files_not_ending_in_zero("C:\\Users\\ferna\\Downloads\\tiles")