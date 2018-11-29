#!/usr/bin/env python3.6

import sys
import argparse
import yaml
import secrets
from ckanapi import RemoteCKAN, NotAuthorized
from os import path, listdir, symlink, makedirs, readlink
import parsers

with open("config.yml", "r") as c:
    config = yaml.load(c)

api_key = config["API_key"]
host = config["host"]
organization = config["organization"]
trajectory_data_path = config["trajectory_data_path"]
public_data_path = config["public_data_path"]
public_hostname = config["public_hostname"]

user_agent = 'atb_update/1.0'
api = RemoteCKAN(
    "http://{}".format(host),
    apikey=api_key,
    user_agent=user_agent
)

def find_all():
    """Finds all datasets in the database"""
    return api.action.package_show()

def delete_all(datasets):
    for dataset in datasets:
        api.action.package_delete(id = dataset)

def purge_all(datasets):
    for dataset in datasets:
        api.action.dataset_purge(id = dataset)

def main():
    confirm = input("Are you sure you want to delete all datasets? They can be recovered from the trash afterwards. Type 'yes' to confirm.")
    datasets = find_all()
    print (datasets)
    if confirm == 'yes':
        delete_all(datasets)
    else:
        print ('Canceling delete')
    confirm = input("Are you sure you want to purge all datasets? They will be gone FOREVER! Type 'yes' to confirm.")
    if confirm == 'yes':
        input("Are you sure? Type 'sure' to confirm. ")
        if confirm == 'sure':
            purge_all(datasets)
    else:
        print ('Canceling purge')

main()