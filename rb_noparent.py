from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional
import sys
import math

DEBUG_NUM = 30

from red_black import Colour, eprint, RbNodeBase, RbTree

# Idea: eliminate the need for parent pointers, by having a list of traversed
# parents that you construct as you insert a node. You can allocate that only once if you like.
# It's from Facebook's 2011 jemalloc blog post.
# https://www.facebook.com/notes/10158791475077200/
# What does the post mean when they say "lazy" rebalancing?

class ParentlessRbNode(RbNodeBase):
    pass

class ParentlessRbTree(RbTree):
    def __init__(self):
        self.root = None
        self.size = 0

    def _dir_rotate(self, G: Optional[ParentlessRbNode], P: ParentlessRbNode, right: bool):
        left = not right
        S = P.get_child(left)
        assert(S is not None)
        C = S.get_child(right)
        P.set_child(C, left)
        S.set_child(P, right)
        if G is not None:
            G.set_child(S, P is G.right)
        else:
            self.root = S
        return S

    def _bst_insert_flat(self, data: Any, debug=False):
        node = self.root
        is_right = False
        stack = []
        while node is not None:
            stack.append(node)
            if data < node.item:
                node = node.left
                is_right = False
            elif data == node.item:
                return
            else:
                node = node.right
                is_right = True
        if debug:
            print(self.graphviz("PreInsert", str(data)))
        # now we know the item isn't already in the tree
        self.size += 1
        self.rb_insert(stack, data, is_right, debug)
        if debug:
            print(self.graphviz("Done"))

    def rb_insert(self, stack: list[ParentlessRbNode], data: Any, is_right: bool, debug=False):
        N = ParentlessRbNode(data)
        def uncle(g, p):
            return (g.right if p == g.left else g.left)
        P = stack.pop() if stack else None
        if P is None:
            self.root = N
            # Maintain root/nil is black invariant
            self.root.colour = Colour.BLACK
            return
        P.set_child(N, is_right)
        G = None
        U = None
        GP = None
        # now restore the red black balance by walking up from N to the top, rotating
        while True:
            if debug:
                print(self.graphviz("Iter", str(N.item)))
            if P.colour is Colour.BLACK:
                # Case_I3: P black
                return
            G = stack.pop() if stack else None
            if G is None:
                # Case_I6: P is root and red
                P.colour = Colour.BLACK
                return
            # else: P red and G!=NULL.
            U = uncle(G, P)
            if U is None or U.colour == Colour.BLACK:
                # Case_I45: P red && U black
                P_right = P is G.right
                if N is P.get_child(not P_right):
                   # Case_I4 (P red && U black && N inner grandchild of G):
                   self._dir_rotate(G, P, P_right)
                   N = P
                   P = G.get_child(P_right) # new parent of N (not G! we rotated!)
                   # fall through to Case_I5
                # Case_I5 (P red && U black && N outer grandchild of G):
                P.colour = Colour.BLACK
                G.colour = Colour.RED
                GP = stack[-1] if stack else None
                self._dir_rotate(GP, G, not P_right); # G may be the root
                return # insertion complete
            # Case_I1 (P+U red):
            P.colour = Colour.BLACK
            U.colour = Colour.BLACK
            G.colour = Colour.RED
            if stack:
                N = G
                P = stack.pop()
            else:
                return


if __name__ == "__main__":
    import random

    tree = ParentlessRbTree()
    vals = list(range(500))
    random.shuffle(vals)
    j = 0
    for i in vals:
        tree.insert(i, debug= (j == 30))
        j += 1

    s = sorted(vals)
    assert(tree.to_list() == s)
    # assert(tree.max_depth() <= 2 * math.log2(len(vals) + 1))
    # assert(tree.contains(505))
    # assert(not tree.contains(-100000))

