from __future__ import division
import sh
import os
import scipy.optimize
import itertools
import math
import re
from collections import Counter, defaultdict
from pprint import pprint
import random

from sum_product import SumProduct, NormalizingConstant
from demography import Demography

scrm = sh.Command(os.environ["SCRM_PATH"])

def test_joint_sfs_inference():
    #return True
    newick_tpl = """
        ((a:{t0:f}[&&momi:model=constant:N={N0:f}:lineages=1],
          b:{t0:f}[&&momi:model=constant:N={N0:f}:lineages=1]):{rt0:f},
         c:{t1:f}[&&momi:model=constant:N={N0:f}:lineages=1])[&&momi:model=constant:N={N0:f}];
    """
    N0=1.0
    theta=1.0
    t0=random.uniform(.25,2.5)
    t1= t0 + random.uniform(.5,5.0)
    jsfs = run_scrm(N0, theta, t0, t1)
    pprint(dict(jsfs))
    def f(join_time):
        print(join_time)
        tree = newick_tpl.format(t0=join_time, N0=N0, t1=t1, rt0=t1 - join_time)
        demo = Demography.from_newick(tree)
        totalSum = NormalizingConstant(demo).normalizing_constant()
        ret = 0.0
        for states, weight in sorted(jsfs.items()):
            st = {a: {'derived': b, 'ancestral': 1 - b} for a, b in zip("abc", states)}
            demo.update_state(st)
            sp = SumProduct(demo)
            print(weight, states, sp.p(), totalSum)
            ret -= weight * math.log(sp.p() / totalSum)
            #ret -= weight * math.log(sp.p())
        return ret
    #f(t0)
    res = scipy.optimize.fminbound(f, 0, t1, xtol=.1)
    #res = scipy.optimize.minimize(f, random.uniform(0,t1), bounds=((0,t1),))
    #assert res == t0
    assert abs(res - t0) / t0 < .95
#    print (res, t0, t1)
#    print(res.x, t0, t1)

def test_jeff():
    return True
    states = """170.00000       A:nean human chimp      D:sima deni
    124.00000       A:deni nean chimp       D:human sima
    231.00000       A:chimp sima    D:human nean deni
    1055.00000      A:chimp deni human sima D:nean
    1300.00000      A:chimp D:human sima nean deni
    136.00000       A:deni human chimp      D:sima nean
    157.00000       A:chimp nean sima       D:human deni
    1094.00000      A:chimp deni nean sima  D:human
    202.00000       A:chimp deni sima       D:human nean
    121.00000       A:nean chimp    D:sima human deni
    1178.00000      A:chimp nean human sima D:deni
    181.00000       A:chimp human sima      D:nean deni
    129.00000       A:human chimp   D:sima nean deni
    142.00000       A:deni chimp    D:human sima nean"""
    linere = re.compile(r"([0-9.]+)\s+A:([^D]*)D:(.*)$")
    st = []
    for line in states.split("\n"):
        weight, ancestral, derived = linere.match(line.strip()).groups()
        weight = float(weight)
        ancestral = ancestral.strip().split()
        derived = derived.strip().split()
        d = {k: {'ancestral': 1, 'derived': 0} for k in ancestral}
        d.update({k: {'ancestral': 0, 'derived': 1} for k in derived})
        if len(derived) > 1:
            st.append((weight, d, line))
    def f(j):
        newick_tpl = """((((nean:0.600000{params},deni:0.600000{params}):{nean_deni_j:f},sima:{sima_j:f}{params}):{j:f},human:0.800000{params}):7.200000,chimp:8.000000{params});"""
        newick = newick_tpl.format(params="[&&momi:model=constant:N=1:lineages=1]", j=j, sima_j=.8 - j, nean_deni_j=.2 - j)
        demo = Demography.from_newick(newick)
        ret = 0.0
        for weight, states, line in sorted(st):
            demo.update_state(states)
            sp = SumProduct(demo)
            ret -= weight * math.log(sp.p())
            print(line, math.log(sp.p()))
        print(j)
        return ret
    res = scipy.optimize.minimize_scalar(f, method="bounded", bounds=(0, 0.2))
    print(res.x)


def run_scrm(N0, theta, t0, t1):
    t0 /= 2. * N0
    t1 /= 2. * N0
    scrm_args = [3, 50000, '-t', theta, '-I', 3, 1, 1, 1, '-ej', t1, 2, 3, '-ej', t0, 1, 2]
    print(scrm_args)
    def f(x):
        if x == "//":
            f.i += 1
        return f.i
    f.i = 0
    runs = itertools.groupby((line.strip() for line in scrm(*scrm_args)), f)
    next(runs)
    c = Counter()
    for i, lines in runs:
        lines = list(lines)
        assert lines[0] == "//"
        nss = int(lines[1].split(":")[1])
        dd = [0] * 3
        if nss == 0:
            continue
        for i, line in enumerate(lines[3:(3 + 3)]):
            dd[i] += int(line[0])
        assert sum(dd) > 0
        c[tuple(dd)] += 1 
    return c


if __name__ == "__main__":
    # test_jeff()
    test_joint_sfs_inference()
