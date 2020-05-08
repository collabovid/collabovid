#!/bin/bash

# Path that should be builded
path=$1

# Name of the environment that should be outputted in dist directory
env=$2

# k8s/dist
output_dir=$(dirname "$0")/dist

# e.g. k8s/dist/dev
env_path=$output_dir/$env

# build the specified path with kustomize
kustomize build $path | kubesplit -o $env_path -p

# checks if for a given wildcard expression, the file exists
function wildcard_exists() {
  test -e "$1"
}

# folders where jobs and cronjobs are placed
jobs_dir=$output_dir/jobs/$env
cronjobs_dir=$output_dir/cronjobs/$env

# create dirs and empty dirs
mkdir -p $jobs_dir && rm -rf $jobs_dir/*
mkdir -p $cronjobs_dir && rm -rf $cronjobs_dir/*

# Move jobs and cronjobs to extra folder

if wildcard_exists $env_path/job*; then
  mv $env_path/job* $output_dir/jobs/$env/
fi

if wildcard_exists $env_path/cronjob*; then
  mv $env_path/cronjob* $output_dir/cronjobs/$env/
fi
