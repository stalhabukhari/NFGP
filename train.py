import os
import yaml
import time
import argparse
import importlib
import os.path as osp
from utils import AverageMeter, dict2namespace, update_cfg_hparam_lst
import torch
#from torch.backends import cudnn
from torch.utils.tensorboard import SummaryWriter


assert torch.cuda.is_available(), "No CUDA device detected. Exiting..."


def get_args():
    # command line args
    parser = argparse.ArgumentParser(
        description='Flow-based Point Cloud Generation Experiment')
    parser.add_argument('config', type=str,
                        help='The configuration file.')

    # distributed training
    parser.add_argument('--gpu', default=None, type=int,
                        help='GPU id to use. None means using all '
                             'available GPUs.')

    # Resume:
    parser.add_argument('--resume', default=False, action='store_true')
    parser.add_argument('--pretrained', default=None, type=str,
                        help="Pretrained cehckpoint")

    # Test run:
    parser.add_argument('--test_run', default=False, action='store_true')

    # Hyper parameters
    parser.add_argument('--hparams', default=[], nargs="+")
    args = parser.parse_args()

    # parse config file
    with open(args.config, 'r') as f:
        config = yaml.load(f, Loader=yaml.Loader)
    config = dict2namespace(config)
    config, hparam_str = update_cfg_hparam_lst(config, args.hparams)

    # Currently save dir and log_dir are the same
    if not hasattr(config, "log_dir"):
        #  Create log_name
        cfg_file_name = os.path.splitext(os.path.basename(args.config))[0]
        run_time = time.strftime('%Y-%b-%d-%H-%M-%S')
        post_fix = hparam_str + run_time

        config.log_name = "logs/%s_%s" % (cfg_file_name, post_fix)
        config.save_dir = "logs/%s_%s" % (cfg_file_name, post_fix)
        config.log_dir = "logs/%s_%s" % (cfg_file_name, post_fix)

        os.makedirs(osp.join(config.log_dir, 'config'))
        with open(osp.join(config.log_dir, "config", "config.yaml"), "w") as outf:
            yaml.dump(config, outf)
    return args, config


def main_worker(cfg, args):
    # basic setup
    # cudnn.benchmark = True

    writer = SummaryWriter(log_dir=cfg.log_name)
    data_lib = importlib.import_module(cfg.data.type)
    loaders = data_lib.get_data_loaders(cfg.data, args)
    train_loader = loaders['train_loader']
    test_loader = loaders['test_loader']
    trainer_lib = importlib.import_module(cfg.trainer.type)
    trainer = trainer_lib.Trainer(cfg, args)

    start_epoch = 0
    start_time = time.time()

    if args.resume:
        if args.pretrained is not None:
            start_epoch = trainer.resume(args.pretrained)
        else:
            start_epoch = trainer.resume(cfg.resume.dir)

    # If test run, go through the validation loop first
    if args.test_run:
        trainer.save(epoch=-1, step=-1)
        val_info = trainer.validate(test_loader, epoch=-1)
        trainer.log_val(val_info, writer=writer, epoch=-1)

    # main training loop
    print("Start epoch: %d End epoch: %d" % (start_epoch, cfg.trainer.epochs + start_epoch))
    step = 0
    duration_meter = AverageMeter("Duration")
    loader_meter = AverageMeter("Loader time")
    for epoch in range(start_epoch, cfg.trainer.epochs + start_epoch):

        # train for one epoch
        loader_start = time.time()
        for bidx, data in enumerate(train_loader):
            loader_duration = time.time() - loader_start
            loader_meter.update(loader_duration)
            step = bidx + len(train_loader) * epoch + 1
            logs_info = trainer.update(data)
            if step % int(cfg.viz.log_freq) == 0 and int(cfg.viz.log_freq) > 0:
                duration = time.time() - start_time
                duration_meter.update(duration)
                start_time = time.time()
                print("Epoch %d Batch [%2d/%2d] Time [%3.2fs] Loading [%3.2fs]"
                      " Loss %2.5f"
                      % (epoch, bidx, len(train_loader), duration_meter.avg,
                         loader_meter.avg, logs_info['loss']))
                visualize = step % int(cfg.viz.viz_freq) == 0 and \
                            int(cfg.viz.viz_freq) > 0
                trainer.log_train(
                    logs_info, data,
                    writer=writer, epoch=epoch, step=step, visualize=visualize)

            # Reset loader time
            loader_start = time.time()

        # Save first so that even if the visualization bugged,
        # we still have something
        if (epoch + 1) % int(cfg.viz.save_freq) == 0 and \
                int(cfg.viz.save_freq) > 0:
            trainer.save(epoch=epoch, step=step)

        if (epoch + 1) % int(cfg.viz.val_freq) == 0 and \
                int(cfg.viz.val_freq) > 0:
            val_info = trainer.validate(test_loader, epoch=epoch)
            trainer.log_val(val_info, writer=writer, epoch=epoch)

        # Signal the trainer to cleanup now that an epoch has ended
        trainer.epoch_end(epoch, writer=writer)
    trainer.save(epoch=epoch, step=step)
    writer.close()


if __name__ == '__main__':
    # command line args
    args, cfg = get_args()

    print("Arguments:")
    print(args)

    print("Configuration:")
    print(cfg)

    main_worker(cfg, args)
