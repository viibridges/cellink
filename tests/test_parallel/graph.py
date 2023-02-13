import sys
sys.path.append('.')

from lib.node import *
from lib.registry import hook_parent
import time

class Root(NodeSI):
    def __str__(self):
        return 'root'

    @classmethod
    def make_root(cls):
        att = cls()
        return att
    
    def forward(self):
        return True

class BaseWorker:
    workload = 0.2
    def forward(self):
        node_name = type(self).__name__

        start_time = time.time()
        local_time = time.localtime(start_time)
        start_working_str = f"Worker    {node_name} Start at {local_time.tm_hour}-{local_time.tm_min}-{local_time.tm_sec}."
        print(start_working_str)

        time.sleep(self.workload)

        end_time = time.time()
        local_time = time.localtime(end_time)
        time_pass = end_time - start_time
        end_working_str = f"Worker    {node_name} Finish at {local_time.tm_hour}-{local_time.tm_min}-{local_time.tm_sec}, Spend Time {time_pass}s."
        print(end_working_str)
        print()
        return True


@hook_parent(Root)
class A(BaseWorker, NodeSI):
    pass

@hook_parent(Root)
class B(BaseWorker, NodeSI):
    pass

@hook_parent(A)
class C(BaseWorker, NodeSI):
    pass

@hook_parent(A)
class D(BaseWorker, NodeSI):
    pass

@hook_parent(A)
class E(BaseWorker, NodeSI):
    pass

@hook_parent(B)
class F(BaseWorker, NodeSI):
    pass

@hook_parent(B)
class G(BaseWorker, NodeSI):
    pass

@hook_parent(E, F)
class H(BaseWorker, NodeMI):
    pass

@hook_parent(C, D)
class I(BaseWorker, NodeMI):
    pass

@hook_parent(Root)
class J(BaseWorker, NodeSI):
    pass

@hook_parent(J, I, H)
class K(BaseWorker, NodeMI):
    pass

@hook_parent(I, F, G)
class L(BaseWorker, NodeMI):
    pass

@hook_parent(J, C)
class M(BaseWorker, NodeMI):
    pass

class N(BaseWorker, NodeSI):
    pass

@hook_parent(N)
class O(BaseWorker, NodeSI):
    pass

@hook_parent(O)
class P(BaseWorker, NodeSI):
    pass

@hook_parent(O)
class Q(BaseWorker, NodeSI):
    pass

@hook_parent(Q, M)
class R(BaseWorker, NodeMI):
    pass

@hook_parent(P)
class S(BaseWorker, NodeSI):
    pass

@hook_parent(P)
class T(BaseWorker, NodeSI):
    pass

@hook_parent(S, T)
class U(BaseWorker, NodeMI):
    pass


@hook_parent(K, R, U)
class V(BaseWorker, NodeMI):
    pass