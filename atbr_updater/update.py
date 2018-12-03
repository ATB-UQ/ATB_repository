#!/usr/bin/env python3.6

import sys
import argparse
import yaml
import secrets
from ckanapi import RemoteCKAN, NotAuthorized
from os import path, listdir, symlink, makedirs, readlink
import parsers
from parsers import RunData

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
    failed_datasets = []

    for dataset, dataset_path in zip(datasets, dataset_paths):
        print ("Processing "+dataset+"...")
        try:
            update_dataset(
                dataset,
                dataset_path,
                trajectory_data_path,
                public_data_path,
                organization,
                public_hostname,
            )
        except Exception as e:
            print (dataset + " failed, is " + str(e))
            failed_datasets.append(dataset)
            continue
        print("Updated "+dataset)
    with open('errors.txt', 'w') as file:
        for dataset in failed_datasets:
            file.write(dataset + '\n')

def param2extras(parameters):
    extra_dict = {}
    extra_params = []
    used_params = ['pressure', 'runtime', 'simulation_time', 'temperature']
    for key in parameters:
        if key in used_params:
            value = parameters[key]
            extra_params.append({'key': key, 'value': value})
    extra_dict['extras'] = extra_params
    return extra_dict

def where_in(name, value, big_range):
    """Determines which bucket of big_range 'value' lies in."""
    bottom = big_range[0]
    top = big_range[1]
    step = big_range[2]
    i = 0
    bot_range = bottom + i * step

    while bot_range < top:
        bot_range = bottom + i * step
        top_range = bottom + (i + 1) * step
        i += 1
        if value >= bot_range and value < top_range:
            tag = name +  " {0}-{1}".format(bot_range, top_range)
            return tag

def at_least(name, value, checkpoints):
    """Returns a string stating the largest checkpoint value is greater than. DO NOT USE FOR NEGATIVE NUMBERS"""
    checkpoints.insert(0, 0)
    for checkpoint in checkpoints:
        if checkpoint <= value:
            maximum = checkpoint
    tag = "Min" + name + " is {}".format(maximum)
    return tag

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
    try:
        program = config["program"]
    except KeyError:
        program = []

    parameters = dataset_control(dataset_path, trajectory_data_path, program)
    parameter_tags = ['num_atoms', 'barostat', 'thermostat', 'temperature', 'runtime', 'box_side']

    for tag in parameter_tags:
        try:
            value = parameters[tag]
            if (type(value) is not int) or (value >= 0):
                if tag is 'temperature':
                    try:
                        value = where_in('Temperature', value, (200, 400, 10))
                    except TypeError:
                        value = float(value)
                        value = where_in('Temperature', value, (200, 400, 10))
                        value = value + ' K'
                elif tag is 'runtime':
                    value = at_least('Run time', value, [0.01, 0.1, 1, 10, 100, 1000])
                    value = value + ' ns'
                elif tag is 'num_atoms':
                    value = at_least('NumAtoms', value, [10, 100, 1000, 10000])
                elif tag is 'box_side':
                    value = at_least('BoxSize', value, [0.1, 1, 10, 100, 1000, 10000])
                else:
                    value = tag + ' is ' + value
                tags.append(dict(name=value))
        except KeyError:
            continue

    try:
        package_data = api.action.package_show( id = dataset.lower() )
    except:
        print("Creating "+dataset+"...")
        create_dataset(dataset, dataset_path, organization)
        package_data = api.action.package_show( id = dataset.lower() )

    del package_data['extras']
    updated_data = { **package_data, **config, **parameters}

    dataset_dir = path.join(trajectory_data_path, dataset_path)
    public_dataset_dir = path.join(trajectory_data_path, dataset)
    subdirs = [ d for d in listdir(dataset_dir) if not (d=="atbrepo.yml" or d=="metadata.yml")]
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

    dataset = api.action.package_update(**updated_data)
    package_dict = dict(package = dataset)
    api.action.package_create_default_resource_views(**package_dict)

    return updated_data

def has_tag(tag_data, existing_tags):
    vid = "vocabulary_id"

    for existing_tag in existing_tags:
        if existing_tag["name"] == tag_data["name"]:
            if vid in existing_tag and vid in tag_data:
                if existing_tag[vid] == tag_data[vid]:
                    return True
            elif (vid in existing_tag) and (vid not in tag_data):
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
        new_data["format"] = ext
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
    config_path = path.join(trajectory_data_path, dataset_path, "atbrepo.yml")

    if not path.exists(config_path):
        config_path = path.join(trajectory_data_path, dataset_path, "metadata.yml")

    if not path.exists(config_path):
        raw_config = {}
    else:
        try:
            with open(config_path, "r") as c:
                raw_config = yaml.load(c)
        except FileNotFoundError:
            raise Exception("missing config file")
    USE_KEYS = ("title", "notes", "author", "author_email", "program")
    config = { #dictionary of the metadata
        key:raw_config[key] \
            for key in raw_config if key in USE_KEYS
    }
    try:
        tags = [ dict(name=tag) for tag in raw_config["tags"] ] #creates a list of dictionaries of form {name=tag}
    except KeyError:
        tags = [] #If missing tags, just has none
   #special_tags = raw_config["special_tags"]
   #for tag_type in special_tags:
   #    tags.append( dict(name=special_tags[tag_type], vocabulary_id=tag_type) )

    if not "title" in config:
        config["title"] = dataset
    return config, tags

def dataset_control(dataset_path, trajectory_data_path, program):
    control_dir = path.join(trajectory_data_path, dataset_path, 'control')
    energy_dir = path.join(trajectory_data_path, dataset_path, 'energy')
    log_dir = path.join(trajectory_data_path, dataset_path, 'log')

    #gets data from first file in control directory, assuming that all runs have same parameters.
    try:
        control_file = path.join(control_dir, listdir(control_dir)[0])
    except IndexError:
        raise Exception("missing control file")
    except PermissionError:
        raise Exception("missing permissions")
    try:
        log_file = path.join(log_dir, listdir(log_dir)[0])
    except IndexError:
        raise Exception("missing log file")
    except PermissionError:
        raise Exception("missing permissions")
    try:
        energy_file = path.join(energy_dir, listdir(energy_dir)[0])
    except IndexError:
        raise Exception("missing energy file")
    except PermissionError:
        raise Exception("missing permissions")

    files = [control_file, log_file, energy_file]

    parameters = {}

    if not program: #checks if list is empty
        program = []
        type_find = RunData(*files)
        program.append(type_find.get_type())

    if 'AMBER' in program:
        data = parsers.AmberData(*files)
        parameters = data.get_parameters()
    elif 'GROMOS' in program:
        data = parsers.GromosData(*files)
        parameters = data.get_parameters()

    elif 'GROMACS' in program:
        data = parsers.GromacsData(*files)
        parameters = data.get_parameters()

    simulation_time = len(listdir(control_dir)) * parameters['runtime']
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
    if not ("atbrepo.yml" or "metadata.yml") in listdir(args.dir):
        sys.stderr.write("No atbrepo.yml or metadata.yml file found in "+args.dir+"\n")
        exit(1)
    update_dataset(
        path.basename(args.dir),
        path.relpath(args.dir, trajectory_data_path),
        trajectory_data_path,
        public_data_path,
        organization,
        public_hostname,
    )
