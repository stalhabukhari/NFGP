import time
import trimesh
import argparse
import numpy as np
from pathlib import Path


def load_data_for_obj(data_dir, obj_name, obj_inst):
    # nglod format
    pts = np.load(data_dir / obj_name / f"{obj_inst}-pts.npy")
    sdf = np.load(data_dir / obj_name / f"{obj_inst}-sdf.npy")
    mesh_f = np.load(data_dir / obj_name / f"{obj_inst}-mesh_f.npy")
    mesh_v = np.load(data_dir / obj_name / f"{obj_inst}-mesh_v.npy")
    return pts, sdf, mesh_f, mesh_v


def save_data_for_obj(data_dir, obj_name, obj_inst, pts, sdf, mesh_f, mesh_v):
    # nfgp format
    mesh = trimesh.Trimesh(vertices=mesh_v, faces=mesh_f)
    sdf_dataset = {
        'points': pts,
        'sdf': sdf,
        "mesh": mesh
    }
    
    obj_inst_dir = data_dir / obj_name / obj_inst
    obj_inst_dir.parent.mkdir(exist_ok=True)
    obj_inst_dir.mkdir(exist_ok=True)
    
    out_path = obj_inst_dir / "sdf.npy"
    np.save(out_path, sdf_dataset)
    
    mesh_path = obj_inst_dir / "mesh.obj"
    mesh.export(str(mesh_path))


def convert(data_dir: Path, save_dir: Path):
    for objdir in data_dir.glob("*"):
        objcat = objdir.name
        for pts_filepath in objdir.glob("*-pts.npy"):
            obj_inst = pts_filepath.stem.split("-")[0]
            pts, sdf, mesh_f, mesh_v = load_data_for_obj(data_dir, objcat, obj_inst)
            
            print(f"Processing {objcat}: {obj_inst}")
            save_data_for_obj(save_dir, objcat, obj_inst, pts, sdf, mesh_f, mesh_v)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=Path, required=True)
    parser.add_argument("--save_dir", type=Path, required=True)
    args = parser.parse_args()
    
    assert args.data_dir.exists()
    assert args.save_dir.exists()
    
    convert(args.data_dir, args.save_dir)
