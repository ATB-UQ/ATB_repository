#!/usr/bin/env python3.6

import yaml
import secrets
from ckanapi import RemoteCKAN, NotAuthorized
from os import path, listdir, symlink, makedirs

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

def update_repository(
    api,
    trajectory_data_path,
    public_data_path,
    organization,
    public_hostname,
):
    dataset_paths = find_datasets(trajectory_data_path)
    datasets = [ path.basename(p) for p in dataset_paths ]
    existing_datasets = [
        result["name"] \
        for result in api.action.package_search(include_private=True)["results"]
    ]
    for dataset, dataset_path in zip(datasets, dataset_paths):
        if not dataset.lower() in existing_datasets:
            create_dataset(dataset, dataset_path, organization)

    for dataset in datasets:
        update_dataset(
            dataset,
            dataset_path,
            trajectory_data_path,
            public_data_path,
            organization,
            public_hostname,
        )

def update_dataset(
    dataset,
    dataset_path,
    trajectory_data_path,
    public_data_path,
    organization,
    public_hostname,
):
    dataset_dir = path.join(trajectory_data_path, dataset_path)
    public_dataset_dir = path.join(trajectory_data_path, dataset)
    subdirs = listdir(dataset_dir)
    for s,subdir in enumerate(subdirs):
        existing_resources = [
            res["name"] for res in api.action.package_show(
                id = dataset.lower(),
            )["resources"]
        ]
        update_resources(
            dataset,
            existing_resources,
            path.join(dataset_path, subdir),
            trajectory_data_path,
            public_data_path,
            public_hostname,
        )
            #position_func = lambda run: 1 + s + (run-1) * len(subdir)

    resource_metadata = api.action.package_show(
        id = dataset.lower(),
    )["resources"]
    resource_metadata.sort(
        key = lambda x: (
            x["run"]*len(subdir) + subdirs.index(x["resource_type"])
        )
    )
    resource_order = [
        res["id"] for res in resource_metadata
    ]
    api.action.package_resource_reorder(
        id = dataset.lower(),
        order = resource_order,
    )
#   api.call_action(
#       "package_resource_reorder",
#       dict(
#           id = dataset, 
#           order = resource_order,
#       )
#   )

def update_resources(
    dataset,
    existing_resources,
    resource_dir,
    trajectory_data_path,
    public_data_path,
    public_hostname,
):
    abs_resources_dir = path.join(trajectory_data_path, resource_dir)
    resources  = listdir(abs_resources_dir)
    for resource in resources:
        if not resource in existing_resources:
            public_resource = link_public_resource(
                resource,
                resource_dir,
                trajectory_data_path,
                public_data_path,
            )
            name, sep, ext = resource.partition(".")
            run_str = name.rpartition('_')[-1]

            if run_str.isdigit():
                run = int(run_str)
            else:
                run = 1
                
            create_resource(
                resource,
                public_resource,
                path.join(abs_resources_dir, resource),
                dataset,
                public_hostname,
                resource_type = path.basename(resource_dir),
                #file_format = ext,
                run = run,
            )

        else:
            check_resource(
                dataset,
                resource,
                resource_dir, 
                trajectory_data_path,
                public_data_path,
            )

    return resources

def create_resource(
    resource,
    public_resource,
    abs_path,
    dataset,
    public_hostname,
    resource_type,
    #file_format,
    run = 1,
):

    api.action.resource_create(
        name = resource,
        package_id = dataset.lower(),
        url = path.join("http://", public_hostname, "public_data", public_resource),
        size = path.getsize(abs_path),
        run = run,
        private = True,
        owner_org = organization,
        resource_type = resource_type,
    )

def check_resource(
    dataset,
    resource,
    resources_path, 
    trajectory_data_path,
    public_data_path,
):
    return None


def link_public_resource(
    resource,
    resource_dir, 
    trajectory_data_path,
    public_data_path,
):
    obfusicate = secrets.token_urlsafe(32)
    abs_resource_path = path.join(trajectory_data_path, resource_dir, resource)
    rel_public_resource_path = path.join(
        resource_dir,
        obfusicate,
        resource,
    )
    abs_public_resource_path = path.join(
        public_data_path,
        rel_public_resource_path,
    )
    makedirs(path.dirname(abs_public_resource_path), exist_ok=True)
    symlink(abs_resource_path, abs_public_resource_path)
    return rel_public_resource_path

def create_dataset(dataset, dataset_path, organization):
    if not None == dataset_config(dataset_path, trajectory_data_path):
        with open(path.join(trajectory_data_path, "repo.yml"), "r") as c:
            config = yaml.load(c)
    else:
        config = dict(
            notes = "",
            title = dataset,
        )
    api.action.package_create(
        name = dataset.lower(),
        title = config["title"],
        notes = config["notes"],
        private = True,
        owner_org = organization,
    )
    return dataset

def find_datasets(
    trajectory_data_path,
    found = [],
    top = trajectory_data_path
):
    dirs = listdir(trajectory_data_path)
    if "trajectory" in dirs:
        found.append(path.relpath(trajectory_data_path, top))
    else:
        for directory in dirs:
            found = find_datasets(
                path.join(trajectory_data_path, directory),
                found = found,
                top = top,
            )
    return found




def dataset_config(dataset, trajectory_data_path):
    # placeholder
    return None

update_repository(
    api,
    trajectory_data_path,
    public_data_path,
    organization,
    public_hostname,
)

