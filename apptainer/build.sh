#!/bin/bash
apptainer build -B $(dirname $(pwd)):/code-dir nfgp.sif ApptainerFile