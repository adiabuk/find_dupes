#!/usr/bin/env bash

# Run find_dupes with default reccommended options

if [[ -L ${BASH_SOURCE[0]} ]]; then
  DIR=`readlink ${BASH_SOURCE[0]} | xargs dirname`
else
  DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
fi

$DIR/find_dupes.py --threads=1000 \
                   --ignore_dot_files \
                   --ignore_dot_dirs \
                   --ignore_dirs=tmp,build.initrd \
                   --ignore_files=LICENSE \
                   --minimum_file_size=10000 $@
