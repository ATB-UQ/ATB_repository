import os
from atbr_updater.parse_control_files import *

directory = 'test_files'

file_parameters = {}
i = 0

for file in os.listdir(directory):
    file_path = os.path.join(directory, file)
    current_file = Amber_Data(file_path)
    file_parameters[i] = current_file.get_parameters()
    i += 1

for key in file_parameters:
    print(key, file_parameters[key])
