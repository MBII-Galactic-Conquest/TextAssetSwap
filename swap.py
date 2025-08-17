import os
import sys
import shutil
import zipfile
import json

def resource_path(relative_path):
    """
    Get the absolute path to a resource, works for both
    development and for the pyinstaller-bundled executable.
    """
    try:
        # PyInstaller creates a temporary folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def clear_console():
    """
    Clears the console screen based on the operating system.
    """
    os_name = os.name
    if os_name == 'nt':  # For Windows
        os.system('cls')
    else:  # For macOS and Linux
        os.system('clear')

def backup_pk3(pk3_file, backup_file, dirs_to_clear):
    """
    Creates a backup of the PK3 file and removes specified directories
    from the original file.
    """
    if not os.path.exists(pk3_file):
        print(f"Error: The file '{pk3_file}' was not found.")
        return

    if os.path.exists(backup_file):
        print(f"Warning: A backup file '{backup_file}' already exists. Overwriting...")
        
    try:
        # Create a copy of the original file as a backup
        shutil.copyfile(pk3_file, backup_file)
        print(f"Backup created: '{backup_file}'")
    except IOError as e:
        print(f"Error creating backup file: {e}")
        return

    # Create a temporary file to store the modified PK3
    temp_pk3 = "temp_" + pk3_file
    
    try:
        # Open original PK3 for reading and temporary PK3 for writing
        with zipfile.ZipFile(pk3_file, 'r') as zip_read, zipfile.ZipFile(temp_pk3, 'w', zipfile.ZIP_DEFLATED) as zip_write:
            
            # Iterate through all files in the original PK3
            for item in zip_read.infolist():
                # Check if the file's path is in a directory to be cleared
                should_exclude = False
                for dir_path in dirs_to_clear:
                    if item.filename.startswith(dir_path):
                        should_exclude = True
                        break
                
                # If the file is not in a specified directory, copy it to the new ZIP
                if not should_exclude:
                    # Use a try/except for added robustness
                    try:
                        zip_write.writestr(item.filename, zip_read.read(item.filename))
                    except Exception as e:
                        print(f"Error copying file '{item.filename}': {e}")

            # Now, add a .keep file to each of the empty directories to preserve them
            for dir_path in dirs_to_clear:
                keep_file_path = os.path.join(dir_path, '.keep')
                try:
                    zip_write.writestr(keep_file_path, '')
                    print(f"Added placeholder file to: '{keep_file_path}'")
                except Exception as e:
                    print(f"Error adding placeholder file '{keep_file_path}': {e}")
                        
        print(f"Files removed from '{pk3_file}' as requested.")
        
    except zipfile.BadZipFile:
        print(f"Error: '{pk3_file}' is not a valid ZIP file.")
        os.remove(backup_file) # Clean up the backup if the original is corrupted
        return
    except Exception as e:
        print(f"An error occurred during file modification: {e}")
        os.remove(backup_file)
        return
        
    try:
        # Replace the original PK3 with the modified temporary file
        os.remove(pk3_file)
        os.rename(temp_pk3, pk3_file)
        print(f"The original file '{pk3_file}' has been modified.")
    except Exception as e:
        print(f"Error replacing the original file: {e}")


def restore_pk3(pk3_file, backup_file):
    """
    Restores the PK3 file from the backup.
    """
    if not os.path.exists(backup_file):
        print(f"Error: The backup file '{backup_file}' was not found.")
        return

    if os.path.exists(pk3_file):
        print(f"Removing existing '{pk3_file}'...")
        try:
            os.remove(pk3_file)
        except OSError as e:
            print(f"Error removing file '{pk3_file}': {e}")
            return
            
    try:
        # Rename the backup file back to the original filename
        os.rename(backup_file, pk3_file)
        print(f"Restored from backup: '{pk3_file}'")
    except OSError as e:
        print(f"Error restoring file: {e}")


def main():
    """
    Main function to run the script and present options to the user.
    """
    CONFIG_FILE = 'config.json'
    
    # Check for the config file and load/create it
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                pk3_file_name = config.get('pk3_file')
                if not pk3_file_name:
                    raise ValueError("PK3 file name not found in config file.")
                print(f"Using configured PK3 file: '{pk3_file_name}'")
        except (IOError, json.JSONDecodeError, ValueError) as e:
            print(f"Error reading config file: {e}. Starting first-time setup.")
            pk3_file_name = None
    else:
        pk3_file_name = None

    if not pk3_file_name:
        clear_console()
        print("\nFirst-time setup.")
        pk3_file_name = input("Enter the name of the PK3 file (e.g., MBAssets3.pk3): ")
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'pk3_file': pk3_file_name}, f)
            print(f"Configuration saved to '{CONFIG_FILE}'.")
        except IOError as e:
            print(f"Error saving config file: {e}. Continuing without saving.")

    # Define file names and directories to modify based on the configured PK3 file
    BACKUP_FILE = pk3_file_name + '.bak'
    DIRS_TO_CLEAR = [
        'ext_data/mb2/character/',
        'ext_data/mb2/teamconfig/'
    ]

    while True:
        clear_console()
        print(f"\nPK3 File Manager for '{pk3_file_name}'")
        print("------------------")
        print("1 - Backup (makes a copy and modifies the original)")
        print("2 - Restore Backup (replaces original with the backup)")
        print("3 - Use another PK3 file")
        print("4 - Exit")

        choice = input("Enter your choice (1, 2, 3, or 4): ")

        if choice == '1':
            backup_pk3(pk3_file_name, BACKUP_FILE, DIRS_TO_CLEAR)
            input("Press Enter to continue...")
        elif choice == '2':
            restore_pk3(pk3_file_name, BACKUP_FILE)
            input("Press Enter to continue...")
        elif choice == '3':
            new_pk3_file = input("Enter the new PK3 file name: ")
            try:
                with open(CONFIG_FILE, 'w') as f:
                    json.dump({'pk3_file': new_pk3_file}, f)
                print(f"Configuration updated to '{new_pk3_file}'. Please restart the script to apply changes.")
                break # Exit the script to force a fresh start with the new config
            except IOError as e:
                print(f"Error saving new config: {e}. Please try again.")
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

# Run the main function
if __name__ == '__main__':
    main()
