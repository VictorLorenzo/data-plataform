import os

# list json files in directory
def list_files(directory, extension='json'):
    return [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith(f'.{extension}')]

def list_directories(directory):
    return [os.path.join(directory, dir) for dir in os.listdir(directory) if os.path.isdir(os.path.join(directory, dir))]