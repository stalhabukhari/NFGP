import yaml
import time
import argparse
import importlib
from pathlib import Path

import numpy as np
import torch
from rich import print

from utils import dict2namespace, update_cfg_hparam_lst

assert torch.cuda.is_available(), "No CUDA device detected. Exiting..."


def get_args():
    # command line args
    parser = argparse.ArgumentParser(
        description='Flow-based Point Cloud Generation Experiment')

    # Resume:
    parser.add_argument('--dir', type=Path, required=True)
    parser.add_argument('--ckpt', type=Path, required=True)

    # Hyper parameters
    args = parser.parse_args()
    
    args.cfg_filepath = args.dir / 'config' / 'config.yaml'
    args.ckpt_filepath = args.dir / 'checkpoints' / args.ckpt

    # parse config file
    with open(args.cfg_filepath, 'r') as f:
        config = yaml.load(f, Loader=yaml.Loader)
    config = dict2namespace(config)
    return args, config


if __name__ == "__main__":
    args, cfg = get_args()
    
    trainer_lib = importlib.import_module(cfg.trainer.type)
    trainer = trainer_lib.Trainer(cfg, args)
    
    start_epoch = trainer.resume(args.ckpt_filepath)
            
    batch = torch.randn(100, 3).float().cuda()
    out = trainer.net(batch)
    print(out.shape)
    