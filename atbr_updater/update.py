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
    config, tags = dataset_config(dataset, dataset_path, trajectory_data_path)
    package_data = api.action.package_show( id = dataset.lower() )
    updated_data = { **package_data, **config }

    dataset_dir = path.join(trajectory_data_path, dataset_path)
    public_dataset_dir = path.join(trajectory_data_path, dataset)
    subdirs = [ d for d in listdir(dataset_dir) if not d=="metadata.yml" ]
    resources = []
    for s,subdir in enumerate(subdirs):
        resources += update_resources(
            dataset,
            package_data["resources"],
            path.join(dataset_path, subdir),
            trajectory_data_path,
            public_data_path,
            public_hostname,
            organization,
        )
    resources.sort(
        key = lambda x: (
            x["run"]*len(subdir) + subdirs.index(x["resource_type"])
        )
    )
    updated_data["resources"] = resources
    printdict(updated_data) ##DEBUG
    api.action.package_update(**updated_data)
    return updated_data

def update_resources(
    dataset,
    existing_resources,
    resource_dir,
    trajectory_data_path,
    public_data_path,
    public_hostname,
    organization,
):
    abs_resources_dir = path.join(trajectory_data_path, resource_dir)
    resources  = listdir(abs_resources_dir)
    existing_resource_names = [ res["name"] for res in existing_resources ]
    resources_data = []
    for resource in resources:
        abs_resource_path = path.join(abs_resources_dir, resource)
        new_data = dict(
            package_id = dataset.lower(),
            size = path.getsize(abs_resource_path),
            private = True,
            owner_org = organization,
            resource_type = path.basename(resource_dir),
        )
        name, sep, ext = resource.partition(".")
        run_str = name.rpartition('_')[-1]
        if run_str.isdigit():
            run = int(run_str)
        else:
            run = 1
        new_data["run"] = run
        if not resource in existing_resource_names:
            old_data = {"name" : resource}
            public_resource = check_for_link(
                resource,
                resource_dir,
                trajectory_data_path,
                public_data_path,
            )
            if public_resource == None:
                public_resource = link_public_resource(
                    resource,
                    resource_dir,
                    trajectory_data_path,
                    public_data_path,
                )
            new_data["url"] = path.join(
                "http://", public_hostname, "public_data", public_resource
            )
        else:
            old_data = [
                res for res in resources if res[name] == resource
            ][0]
        #printdict(old_data) ##DEBUG
        resources_data.append({**old_data, **new_data})
    return resources_data

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

def check_for_link(
    resource,
    resource_dir,
    trajectory_data_path,
    public_data_path,
):
    abs_resource_path = path.join(trajectory_data_path, resource_dir, resource)
    return None


def create_dataset(dataset, dataset_path, organization):
    api.action.package_create(
        name = dataset.lower(),
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

def dataset_config(dataset, dataset_path, trajectory_data_path):
    config_path = path.join(trajectory_data_path, dataset_path, "metadata.yml")
    if not path.exists(config_path):
        raw_config = {}
    else:
        with open(config_path, "r") as c:
            raw_config = yaml.load(c)
    USE_KEYS = ("title", "notes", "author", "author_email")
    config = {
        key:raw_config[key] \
            for key in raw_config if key in USE_KEYS
    }
    tags = []

    if not "title" in config:
        config["title"] = dataset
    return config, tags
    
def printdict(d):
    print( yaml.dump(d, default_flow_style=False )  )

update_repository(
    api,
    trajectory_data_path,
    public_data_path,
    organization,
    public_hostname,
)

