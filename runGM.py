#!/usr/bin/env python
from mpi4py import MPI

mpi_comm = MPI.COMM_WORLD
mpi_rank = mpi_comm.Get_rank()
mpi_size = mpi_comm.Get_size()
def root_print(*args, **kw):
    if mpi_rank == 0:
        print(*args, **kw)
root_print("mpi_rank: ", mpi_size)
root_print("mpi loaded")

import os
import time
import argparse
import tensorflow as tf
root_print("tensorflow loaded")
from tnsp import SquareLattice
root_print("tnsp loaded")

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--continue', dest='continued', default=False, action="store_true", help="continue run, conflict with -f")
parser.add_argument('-N', '--size-n', dest='n', required=True, type=int, help="system size n")
parser.add_argument('-M', '--size-m', dest='m', required=True, type=int, help="system size m")
parser.add_argument('-d', '--dim', dest='D', required=True, type=int, help="bond dimension")
parser.add_argument('-D', '--dim-cut', dest='D_c', required=True, type=int, help="dimension cut in MPO")
parser.add_argument('-s', '--scan-time', dest='scan_time', required=True, type=int, help="scan time in MPO")
parser.add_argument('-l', '--step-size', dest='step_size', required=True, type=float, help="step size in SU or GM")
parser.add_argument('-m', '--markov', dest='markov', required=True, type=int, help="markov chain length")
parser.add_argument('-f', '--load-from', dest='load_from', help="load from file")
parser.add_argument('-p', '--save-prefix', dest='save_prefix', default='run', help="prefix for saving data")
args = parser.parse_args()

if args.continued and args.load_from != None:
    exit("conflict between --continue and --load-from")

if args.continued and not args.load_from:
    args.load_from = f"{args.save_prefix}/last/last.npz"

root_print("parameter loaded")

sl = SquareLattice([args.n, args.m], D=args.D, D_c=args.D_c, scan_time=args.scan_time, step_size=args.step_size, markov_chain_length=args.markov, load_from=args.load_from, save_prefix=args.save_prefix)
root_print("lattice created")

config = tf.ConfigProto()
config.graph_options.optimizer_options.global_jit_level = tf.OptimizerOptions.ON_2
config.intra_op_parallelism_threads = 1
config.inter_op_parallelism_threads = 1
config.device_count['GPU'] = 0
sess = tf.Session(config=config)
root_print("session created")

if mpi_rank == 0:
    tf.summary.FileWriter(f'{args.save_prefix}/last/', sess.graph)
start = time.time()
sl.grad_descent(sess)
root_print(time.time()-start)
