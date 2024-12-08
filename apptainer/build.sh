#!/bin/bash
rm -f nfgp.sif && \
apptainer build -B $(dirname $(pwd)):/code-dir nfgp.sif ApptainerFile