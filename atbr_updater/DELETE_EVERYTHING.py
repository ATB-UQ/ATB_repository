#!/usr/bin/env python3.6
import yaml
import sys
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
    return api.action.package_list()

def delete_all(datasets):
    for dataset in datasets:
        api.action.package_delete(id = dataset)

def purge_all(datasets):
    for dataset in datasets:
        api.action.dataset_purge(id = dataset)

def main():
    query = input("Type 'delete' to delete all data, or 'purge' to purge it. Deleted data can be recovered, "
                    "but purged cannot.")
    confirm = input("Are you sure? Type 'yes' to confirm.")
    if (query == 'delete') and (confirm == 'yes'):
        datasets = find_all()
        delete_all(datasets)

    elif (query == 'purge' and confirm == 'yes'):
        datasets = find_all()
        purge_all(datasets)
    else:
        print ('Canceling delete')

main()