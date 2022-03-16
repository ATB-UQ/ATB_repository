# This script may be used to help rename the data/files so that they comply with the naming conventions
# accepted on the ATB repository
# **Notes**
# 1. The script needs to be ran from the each of the individual subdirectories (e.g. control, topology etc.) containing the data files
# 2. The script should not be left in the subdirectories after the renaming is completed, instead, they should be removed prior to 
#    uploading to the ATB repository, this is because the upload script (e.g. update_https_orgs_comments.py mentioned in the "Upload"
#    section of README) will not work if they are left in.
# 3. In function rename_folder, the way the script looks for pattern for sequential naming means that it will not work for files that does not
#    have any of the patterns in them 

import argparse
import sys
import os

parser = argparse.ArgumentParser(description='Script to rename files into standard for the ATB repository. Takes a folder containing one file extension and renames according to the argument specifications. This script should be run from the folder containing the files you would like to rename.', epilog='This script was created by Shelley Barfoot, the last edit was 23/12/21.')

# -n option
parser.add_argument('-n', '--naming', required=True, help='select the numbering system for your files. There are three accepted options: number = numbered sequentially i.e. 1, 2, 3 etc; pad = numbered with padding i.e. 00001, 00002, 00003; time = described with time frame i.e. 0-5ns, 5-10ns, 10-15ns etc; single = a run containing only a single file to rename; wall = a run containing two files, one named with "wall" (initial) and one named with "nowall".', choices=['number', 'pad', 'time', 'single', 'wall'])

args = parser.parse_args()
print("Naming =", args.naming)

def rename_folder(searcher):
    '''
    This is the function that does the renaming. It uses the current folder and directory structure, and the specified naming convention for the file sequence (searcher) and renames all the files.

    INPUT
    -----
    searcher >>> string >>> accepted: [number, pad, time, single, wall]

    OUTPUT
    -----
    None (uses os to rename files)
    '''

    #gets the path for the current location
    my_folder = os.getcwd()

    #get specs for the new name
    extension = 0
    precurser = my_folder.split("/")[-2]
    folder = my_folder.split("/")[-1]

    #loop through the files in the directory and make an array
    file_list = []
    for my_file in os.listdir(my_folder):
        if my_file.endswith(".py"):   #ignore files that ends with .py, without this, the script would not work if the .py is found first by os.listdir(my_folder)
            continue
        if extension == 0:
            extension = my_file.split(".")[-1]
        if my_file.endswith(extension):
            file_list.append(my_file)

    #go through the files and name them correctly based on the folder and the searcher
    current_file = 1
    time  = 0
    while len(file_list)!=0: 
        for name in file_list:

            current_file_pad = str(current_file)

            #set up the pattern for sequential naming
            if searcher=='number':
                pattern = "_"+current_file_pad+"."
            elif searcher=='pad':
                pattern = current_file_pad.zfill(5)
            elif searcher=='time':
                pattern = '_' + str(time) + '-'
            elif searcher=='single':
                pattern = '.'
            elif searcher=='wall':
                if current_file == 1:
                    pattern='_wall'
                else:
                    pattern='_nowall'

            if pattern in name:
                #rename the file, print out for transparency
                print("mv {0} {1}_{2}_{3}.{4}".format(name, precurser, folder, current_file_pad.zfill(5), extension))
                os.system("mv {0} {1}_{2}_{3}.{4}".format(name, precurser, folder, current_file_pad.zfill(5), extension))
                file_list.remove(name)

                if searcher=='time':
                    #get the next starting velocity
                    #this just accepts ns at the end but would be a pretty easy fix
                    split_end = name.split("-")
                    split_ns = split_end[-1].split("ns")
                    time = int(split_ns[0])

                current_file += 1
                break
            elif pattern not in name:
                print ("Error, pattern not in file name")
                return None
                

if __name__ == "__main__":
    rename_folder(args.naming)
