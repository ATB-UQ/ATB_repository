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

def update_repository(
    api,
    trajectory_data_path,
    public_data_path,
    organization,
    public_hostname,
):
    dataset_paths = find_datasets(trajectory_data_path)
    datasets = [ path.basename(p) for p in dataset_paths ]

    for dataset, dataset_path in zip(datasets, dataset_paths):
        print("Processing "+dataset+"...")
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
    # dictionary of metadata, tags of dataset
    config, tags = dataset_config(dataset, dataset_path, trajectory_data_path)
    program = config["program"]

    parameters = dataset_control(dataset_path, trajectory_data_path, program)

    try:
        package_data = api.action.package_show( id = dataset.lower() )
    except:
        print("Creating "+dataset+"...")
        create_dataset(dataset, dataset_path, organization)
        package_data = api.action.package_show( id = dataset.lower() )

    # printdict(parameters)
    updated_data = { **package_data, **parameters, **config }
    # printdict(updated_data)

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
    updated_data["private"] = False

    if not "tags" in updated_data:
        updated_data["tags"] = []
    for tag in tags:
        if not has_tag(tag, updated_data["tags"]):
            updated_data["tags"].append(tag)
    api.action.package_update(**updated_data)

    # printdict(api.action.package_show( id = dataset.lower() ))

    return updated_data

def has_tag(tag_data, existing_tags):
    vid = "vocabulary_id"
    for existing_tag in existing_tags:
        if existing_tag["name"] == tag_data["name"]:
            if vid in existing_tag and vid in tag_data:
                if existing_tag[vid] == tag_data[vid]:
                    return True
            elif not (vid in existing_tag or vid in tag_data):
                return True
    return False

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
            private = False,
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
        else:
            old_data = [
                res for res in existing_resources if res["name"] == resource
            ][0]
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
        url = path.join(
            "http://", public_hostname, "public_data", public_resource
        )
        if "url" in old_data and not old_data["url"] == "":
            if not url == old_data["url"]:
                print("WARNING: "+ \
                    "URL in database ({}) does not match repo directory ({})".format(
                        old_data["url"],
                        url,
                    )
                )
        new_data["url"] = url

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

    abs_public_resource_dir = path.join(
        public_data_path,
        resource_dir,
    )
    if not path.exists(abs_public_resource_dir):
        return None

    for obfusicate in listdir(abs_public_resource_dir):
        link = path.join(abs_public_resource_dir, obfusicate, resource)
        if path.exists(link):
            target = readlink(link)
            if target == abs_resource_path:
                return path.join(resource_dir, obfusicate, resource)
            else:
                raise Exception(
                    "link exists but points to wrong path. Link: {} Target: {}".format(
                        link,
                        target,
                    )
                )
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
    USE_KEYS = ("title", "notes", "author", "author_email", "program")
    config = { #dictionary of the metadata
        key:raw_config[key] \
            for key in raw_config if key in USE_KEYS
    }
    tags = [ dict(name=tag) for tag in raw_config["tags"] ] #creates a list of dictionaries of form {name=tag}
   #special_tags = raw_config["special_tags"]
   #for tag_type in special_tags:
   #    tags.append( dict(name=special_tags[tag_type], vocabulary_id=tag_type) )

    if not "title" in config:
        config["title"] = dataset
    return config, tags

def dataset_control(dataset_path, trajectory_data_path, program):
    control_dir = path.join(trajectory_data_path, dataset_path, 'control')
    #gets control data from first file in control directory, assuming that all runs have same parameters.
    control_file = path.join(control_dir, listdir(control_dir)[0])
    parameters = {}
    if 'AMBER' in program:
        data = parsers.AmberData(control_file)
        parameters = data.get_parameters()

    if 'GROMOS' in program:
        data = parsers.GromosData(control_file)
        parameters = data.get_parameters()

    runtime = parameters['runtime']
    simulation_time = len(listdir(control_dir)) * runtime
    parameters['simulation_time'] = simulation_time

    return parameters


def printdict(d):
    print( yaml.dump(d, default_flow_style=False )  )

import argparse
parser = argparse.ArgumentParser()
parser.add_argument(
    "-d", "--dir",
    default="",
    help="Specify a directory to update",
)

args = parser.parse_args()

if args.dir == "":
    update_repository(
        api,
        trajectory_data_path,
        public_data_path,
        organization,
        public_hostname,
    )
else:
    if not path.isdir(args.dir):
        sys.stderr.write("Path is not a directory: " + args.dir + "\n")
        exit(1)
    if not args.dir.startswith(trajectory_data_path):
        sys.stderr.write(
              "Target directory path must start with root trajectory path "+ \
              trajectory_data_path+"\n"
        )
        exit(1)
    if not "metadata.yml" in listdir(args.dir):
        sys.stderr.write("No metadata.yml file foud in "+args.dir+"\n")
        exit(1)
    update_dataset(
        path.basename(args.dir),
        path.relpath(args.dir, trajectory_data_path),
        trajectory_data_path,
        public_data_path,
        organization,
        public_hostname,
    )
