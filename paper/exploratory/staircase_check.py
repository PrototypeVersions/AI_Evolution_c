"""Exploratory check, 2026-10-13 (before PREREGISTRATION_v2): is a high-order
parity much easier to learn one bit at a time than from scratch?

    python paper/exploratory/staircase_check.py

Output from the original run is in paper/exploratory/staircase_check.txt.
"""
import os; os.environ["OPENBLAS_NUM_THREADS"]="1"
import numpy as np, sys, multiprocessing as mp
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from learners.net import MLP
D=32
def batch(rng, sup, n):
    x=rng.integers(0,2,(n,D)).astype(float)*2-1
    y=(np.prod(x[:,sup],axis=1)>0).astype(int)
    return x,y
def steps_to(net, sup, rng, cap, target=0.9):
    ex,ey=batch(np.random.default_rng(999),sup,2000)
    for s in range(1,cap+1):
        x,y=batch(rng,sup,32); net.train_step(x,y)
        if s%25==0 and net.accuracy(ex,ey)>=target: return s
    return cap+1
def job(args):
    seed,d,lr=args
    rng=np.random.default_rng(seed)
    bits=list(rng.choice(D,d,replace=False))
    net=MLP(np.random.default_rng(seed+1),lr=lr,sizes=(32,128,128,2))
    scratch=steps_to(net,bits,rng,4000)
    # staircase: climb from degree 2 up to d, one bit at a time
    net=MLP(np.random.default_rng(seed+1),lr=lr,sizes=(32,128,128,2))
    climb=[]
    for k in range(2,d+1):
        climb.append(steps_to(net,bits[:k],rng,4000))
    return seed,d,lr,scratch,climb
if __name__=="__main__":
    jobs=[(s,d,lr) for lr in [1e-3,3e-3] for d in [3,4,5,6] for s in range(3)]
    with mp.Pool(4) as p:
        for r in p.imap(job,jobs): print(r, flush=True)
