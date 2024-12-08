#!/bin/bash
# conda create -n NFGP python=3.8 -y && \
# conda activate NFGP && \
#conda install -y pytorch==2.0.1 torchvision==0.15.2 pytorch-cuda=11.7 -c pytorch -c nvidia && \
pip install --upgrade pip && \
pip install tensorboard open3d trimesh networkx matplotlib scipy scikit-image scikit-learn \
    send2trash tifffile tqdm pyrender pyglet Pillow pandas ninja imageio ffmpeg mesh-to-sdf==0.0.15 rich
