from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional
import sys
import math

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

DEBUG_NUM = 30

# https://www.cs.auckland.ac.nz/software/AlgAnim/red_black.html

# leaf nodes are black and have item = None

# A red-black tree is a binary search tree which has the following red-black properties:
#    1. Every node is either red or black.
#    2. Every leaf (NULL) is black.
#    3. If a node is red, then both its children are black.
#    4. Every simple path from a node to a descendant leaf contains the same number of black nodes.
#
# (3) implies that on any path from the root to a leaf, red nodes must not be adjacent.
# However, any number of black nodes may appear in a sequence. 

# the black height of a node x is the number of black nodes on any path from,
# but not including, x, to a leaf node.

# lemma: A red-black tree with n internal nodes has height at most 2log(n+1). 

# As with heaps, additions and deletions from red-black trees destroy the
# red-black property, so we need to restore it. To do this we need to look at
# some operations on red-black trees. 

class Colour(Enum):
    RED = 0
    BLACK = 1
    def __str__(self):
        return "red" if self == Colour.RED else "BLACK"
    def flip(self):
        if self is Colour.RED:
            return Colour.BLACK
        else:
            return Colour.RED

@dataclass
class BSTNode:
    item: Any
    left: Optional['RbNode'] = None
    right: Optional['RbNode'] = None

    def set_child(self, node: 'BSTNode', right: bool):
        if right:
            self.right = node
        else:
            self.left = node

    def get_child(self, right: bool) -> Optional['BSTNode']:
        if right:
            return self.right
        else:
            return self.left

    def __repr__(self):
        return f"{self.item}"

    def __str__(self, level=0):
        ret = ""
        if self.left:
            ret += self.left.__str__(level+1)
        ret += "\t" * level + repr(self) + "\n"
        if self.right:
            ret += self.right.__str__(level+1)
        return ret

def is_red(node: Optional['RbNodeBase']):
    if node:
        return node.colour is Colour.RED
    return False

def insert_at_level(lvls, l, k):
    if l > 0:
        L = []
        if len(lvls) >= l:
            L = lvls[l-1]
        else:
            lvls.append(L)
        L.append(k)

@dataclass
class RbNodeBase(BSTNode):
    colour: Colour = Colour.RED

    def __repr__(self):
        return f"{self.item} [{self.colour}]"

    def as_234(self):
        if is_red(self.left) and is_red(self.right):
            return (
                "4",
                [self.left.item, self.item, self.right.item], 
                [self.left.left, self.left.right, self.right.left, self.right.right]
            )
        elif is_red(self.left) and not is_red(self.right):
            return (
                "3L",
                [self.left.item, self.item], 
                [self.left.left, self.left.right, self.right]
            )
        elif not is_red(self.left) and is_red(self.right):
            return (
                "3R",
                [self.item, self.right.item], 
                [self.left, self.right.left, self.right.right]
            )
        else:
            return (None, [self.item], [self.left, self.right])

    def graphviz234(self, reds, arrows, levels, nils, level=0, parent_key=None):
        node_type, items, children = self.as_234()
        items_str = ",".join(map(str, items))
        key_raw = f"{items_str}"
        if node_type:
            key_raw = f"{node_type}({items_str})"
        key = f"\"{key_raw}\""
        insert_at_level(levels, level, key)
        if parent_key:
            arrows.append(f"{parent_key} -> {key}")
        if node_type != None:
            reds.append(key)
        for i in range(len(children)):
            child = children[i]
            if child:
                child.graphviz234(reds, arrows, levels, nils, level + 1, key)
            else:
                # no need for nils when printing a 2-3-4 tree.
                pass
                # nil = f"\"n_{key_raw}_{i}\""
                # nils.append(nil)
                # arrows.append(f"{key} -> {nil};")
                # insert_at_level(levels, level + 1, nil)

    def graphviz(self, reds, arrows, levels, nils, level=0, parent_key=None):
        key = str(self.item)
        insert_at_level(levels, level, key)
        if parent_key:
            arrows.append(f"{parent_key} -> {key}")
        if self.colour is Colour.RED:
            reds.append(key)

        children = [self.left, self.right]
        for i in range(len(children)):
            child = children[i]
            if child:
                child.graphviz(reds, arrows, levels, nils, level + 1, key)
            else:
                nil = f"n_{key}_{i}"
                nils.append(nil)
                arrows.append(f"{key} -> {nil};")
                insert_at_level(levels, level + 1, nil)

@dataclass
class RbNode(RbNodeBase):
    parent: Optional['RbNode'] = None

    def __repr__(self):
        return f"{self.item} [{self.colour}]"

    def get_uncle(self):
        P = self.parent
        if P is not None and self.parent.parent is not None:
            G = self.parent.parent
            if P is G.left:
                return G.right
            else:
                return G.left
        return None

    def is_on_right(self):
        P = self.parent
        assert(P is not None)
        return self is P.right

class RbTree:
    def __init__(self):
        self.root = None
        self.size = 0

    def _dir_rotate(self, P: RbNode, is_right: bool):
        right = is_right
        left = not is_right
        G = P.parent
        S = P.get_child(left)
        assert(S is not None)
        C = S.get_child(right)
        P.set_child(C, left)
        if C is not None:
            C.parent = P
        S.set_child(P, right)
        P.parent = S
        S.parent = G
        if G is not None:
            G.set_child(S, P is G.right)
        else:
            self.root = S
        return S

        # if is_right:
        #     return self._right_rotate(x)
        # else:
        #     return self._left_rotate(x)

    def _left_rotate(self, x: RbNode):
        y = x.right
        x.right = y.left
        y.parent = x.parent
        if x.parent is None:
            self.root = y
        else:
            if x is x.parent.left:
                # x was on the left of its parent
                x.parent.left = y
            else:
                # x was on the right of its parent
                x.parent.right = y
        y.left = x
        x.parent = y
    def _right_rotate(self, y: RbNode):
        x = y.left
        y.left = x.right
        x.parent = y.parent
        if y.parent is None:
            self.root = x
        else:
            if y is y.parent.left:
                # x was on the left of its parent
                y.parent.left = x
            else:
                # x was on the right of its parent
                y.parent.right = x
        x.right = y
        y.parent = x

    def insert(self, data: Any, debug=False):
        if data is None:
            raise "RbTree: cannot insert null data"
        self._bst_insert_flat(data, debug)

    def _bst_insert_flat(self, data: Any, debug=False):
        parent = None
        node = self.root
        is_right = False
        while node is not None:
            parent = node
            if data < node.item:
                node = node.left
                is_right = False
            elif data == node.item:
                return
            else:
                node = node.right
                is_right = True
        N = RbNode(data)
        if debug:
            print(self.graphviz("PreInsert", [str(data)]))
        # now we know the item isn't already in the tree
        self.size += 1
        self.rb_insert(parent, N, is_right, debug)
        if debug:
            print(self.graphviz("Done"))

    def rb_insert(self, P: Optional[RbNode], N: RbNode, is_right: bool, debug=False):
        N.colour = Colour.RED
        N.left = None
        N.right = None
        N.parent = P
        if P is None:
            self.root = N
            return
        P.set_child(N, is_right)
        # now restore the red black balance by walking up from N to the top, rotating
        while True:
            if debug:
                print(self.graphviz("Iter", [str(N.item)]))
            if P.colour is Colour.BLACK:
                # Case_I3: P black
                return
            G = P.parent
            if G is None:
                # Case_I6: P is root and red
                P.colour = Colour.BLACK
                return
            # else: P red and G!=NULL.
            U = N.get_uncle()
            if U is None or U.colour == Colour.BLACK:
                # Case_I45: P red && U black
                P_right = P.is_on_right();
                if N is P.get_child(not P_right):
                   # Case_I4 (P red && U black && N inner grandchild of G):
                   self._dir_rotate(P, P_right)
                   N = P
                   P = G.get_child(P_right) # new parent of N (not G! we rotated!)
                   # fall through to Case_I5
                # Case_I5 (P red && U black && N outer grandchild of G):
                P.colour = Colour.BLACK
                G.colour = Colour.RED
                self._dir_rotate(G, not P_right); # G may be the root
                return # insertion complete
            # Case_I1 (P+U red):
            P.colour = Colour.BLACK
            U.colour = Colour.BLACK
            G.colour = Colour.RED
            N = G
            P = N.parent
            if P is None:
                return

    def to_list(self):
        as_list = []
        self.inorder(lambda data: as_list.append(data))
        return as_list

    def inorder(self, fn):
        stack = []
        cursor = self.root
        while cursor is not None or len(stack) != 0:
            while cursor is not None:
                stack.append(cursor)
                cursor = cursor.left
            if len(stack) != 0:
                popped = stack.pop()
                fn(popped.item)
                cursor = popped.right

    def contains(self, x: Any):
        cursor = self.root
        while cursor is not None:
            if x < cursor.item:
                cursor = cursor.left
            elif x == cursor.item:
                return True
            else:
                cursor = cursor.right

    def max_depth(self):
        return max(self.max_depth_left(), self.max_depth_right())

    def max_depth_right(self):
        stack = []
        cursor = self.root
        maxd = 0
        while cursor is not None or len(stack) != 0:
            while cursor is not None:
                stack.append(cursor)
                cursor = cursor.left
            maxd = max(maxd, len(stack))
            if len(stack) != 0:
                popped = stack.pop()
                cursor = popped.right
        return maxd

    def max_depth_left(self):
        stack = []
        cursor = self.root
        maxd = 0
        while cursor is not None or len(stack) != 0:
            while cursor is not None:
                stack.append(cursor)
                cursor = cursor.right
            maxd = max(maxd, len(stack))
            if len(stack) != 0:
                popped = stack.pop()
                cursor = popped.left
        return maxd

    def check_invariant(self) -> bool:
        stack = []
        black_count = 0
        cursor = self.root
        same_num_black = None
        while cursor is not None or len(stack) != 0:
            while cursor is not None:
                if len(stack) > 0:
                    _, black_count = stack[-1]
                black_count += (1 if cursor.colour is Colour.BLACK else 0)
                stack.append((cursor, black_count))
                cursor = cursor.left
            eprint(stack)
            if same_num_black is None:
                same_num_black = black_count
            if same_num_black != black_count:
                eprint("failed:\n", self.root)
                return False
            if len(stack) != 0:
                popped, black_count = stack.pop()
                # black_count -= (1 if popped.colour is Colour.BLACK else 0)
                cursor = popped.right
        return True

    def graphviz(self, title="G", emph=[]):
        fmt  = f"""
digraph G {{
    graph [ratio=.48, ordering=out];
    node [style=filled, color=black, shape=circle, width=.6 
          fontname=Helvetica, fontweight=bold, fontcolor=white, 
          fontsize=14, fixedsize=false, margin="0.01,0.01" ];
    labelloc="t";
    label="{title}";
        """
        reds = []
        arrows = []
        levels = []
        nils = []
        if self.root:
            self.root.graphviz(reds, arrows, levels, nils)
        for l in range(len(levels)):
            level = levels[l]
            fmt += "    {rank=same; "
            fmt += ", ".join(level)
            fmt += "}\n"

        if len(reds) > 0:
            fmt += "    "
            fmt += ", ".join(reds)
            fmt += " [fillcolor=red];\n"

        if len(nils) > 0:
            fmt += "    "
            fmt += ", ".join(nils)
            fmt += ' [label="NIL", shape=record, width=.2,height=.12, fontsize=7];\n'
        for e in emph:
            if e and e in reds:
                fmt += f"{e} [fillcolor=purple];\n"
            elif e:
                fmt += f"{e} [fillcolor=blue];\n"
        fmt += "    "
        fmt += "\n    ".join(arrows)

        fmt += "\n}"
        return fmt

    def graphviz234(self, title="G", emph=[]):
        fmt  = f"""
digraph G {{
    graph [ratio=.48, ordering=out];
    node [style=filled, color=black, shape=circle, width=.6 
          fontname=Helvetica, fontweight=bold, fontcolor=white, 
          fontsize=14, fixedsize=false, margin="0.01,0.01" ];
    labelloc="t";
    label="{title}";
        """
        reds = []
        arrows = []
        levels = []
        nils = []
        if self.root:
            self.root.graphviz234(reds, arrows, levels, nils)
        for l in range(len(levels)):
            level = levels[l]
            fmt += "    {rank=same; "
            fmt += ", ".join(level)
            fmt += "}\n"

        if len(reds) > 0:
            fmt += "    "
            fmt += ", ".join(reds)
            fmt += " [fillcolor=red, shape=ellipse];\n"

        if len(nils) > 0:
            fmt += "    "
            fmt += ", ".join(nils)
            fmt += ' [label="NIL", shape=record, width=.2,height=.12, fontsize=7];\n'
        for e in emph:
            if e and e in reds:
                fmt += f"{e} [fillcolor=purple];\n"
            elif e:
                fmt += f"{e} [fillcolor=blue];\n"
        fmt += "    "
        fmt += "\n    ".join(arrows)

        fmt += "\n}"
        return fmt

if __name__ == "__main__":
    import random

    tree = RbTree()
    vals = list(range(500))
    # random.shuffle(vals)
    j = 0
    for i in vals:
        tree.insert(i, debug= (j == 11))
        j += 1

    s = sorted(vals)
    assert(tree.to_list() == s)
    assert(tree.max_depth() < 2 * math.log2(len(vals) + 1))
    # assert(tree.contains(505))
    # assert(not tree.contains(-100000))

