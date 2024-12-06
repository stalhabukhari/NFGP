#!/bin/bash
apptainer run --nv -B "$(dirname $(pwd))":"/code-dir" nfgp.sif \
    "cd /code-dir && ls -l && pip list | grep torch"