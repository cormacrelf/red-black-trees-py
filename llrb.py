from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional, TypeVar
import sys
import math

DEBUG_NUM = 30

from red_black import Colour, eprint, RbNodeBase, RbTree, is_red

# LLRB is a 2-3 or 2-3-4 tree, but the 3-nodes can only lean to the left.
#
#
# 2-nodes are just single nodes with both children ('2 of them') black or nil.
#
#   $
#  / \
# *   *
#
# There are only 3-nodes in this shape, left leaning:
#
#      $
#    // \
#   $    *
#  /\ 
# *  *
#
# i.e. the left node is red, right node is black. Conceptually the top and left
# nodes form a single 3-node where the top one has 1 spare branch and the left
# one has the other 2, making 3.
#
# 4-nodes look like this:
#
#      $
#    // \\
#   $     $
#  /\     /\
# *  *   *  *
#
# This means there is a 1-1 correspondence with a 2-3 or 2-3-4 tree, whereas a
# normal Red-Black Tree has two kinds of 3-node.
#
# Three RB Invariants
# - No path from the root to the bottom contains two consecutive red links.
# - The number of black links on every such path is the same.
# - (LL bonus) no right leaning 3 nodes

class LLRBNode(RbNodeBase):
    def flip_colours(self):
        """
        Flips self, and both child nodes. Never call on a non-full node.
        A color flip obviously does not change the number of black links on any
        path from the root to the bottom, but it may introduce two consecu-
        tive red links higher in the tree, which must be corrected.

        Preserves black link balance under h;
        Passes a RED link up the tree
        Reduces problem to inserting that red link into parent.

            - If parent is a 2-node, you just have to make sure when you create
              the 3-node that if it is right leaning, you rotate it left.
            - If parent is a 3-node, which must be left-leaning, then flipping
              the 4-node three cases:
                - #1 Two consecutive reds in left-left direction, when
                  inserting on leftmost branch of a 3-node. Rotate the top node
                  right.
                - #2 Two consecutive reds in left-right zig-zag, when inserting on
                  middle branch. Rotate the middle node of the zig zag left, to reduce to case #1.
                - #3 It turns into a 4-node if you insert on the rightmost branch.

        For a 2-3-4 tree, it suffices to split any 4-nodes on the way down,
        which may leave right-leaning red or two reds in a row higher up in the
        tree, but you rotate them on the way back up.

        For a 2-3 tree, you have to correct the resulting 4-node from case #3
        after inserting, because it can't stay in the tree permanently.

        Inserting:
        - search as usual
        - if key not found insert new red node at the bottom
        - [*] might leave either right leaning 3-node or two reds in a row
          (either shape) higher up in the tree

        Split 4-nodes on the way down the tree:
        - flip colour
        - [*] might leave either right leaning 3-node or two reds in a row
          (either shape) higher up in the tree

        HENCE, NEW TRICK: Do rotates on the way UP the tree.
            - left-rotate any right-leaning link on search path
            - right-rotate top link if two reds in a row found
            - this happens to cover left-then-right when you have zig zag.
            - trivial with recursion (do it after recursive calls)
            - no corrections needed elsewhere

        Why does moving the colour flip to after the rotations, i.e. on the way up, give you a 2-3 tree?
        Insert in 2-3 tree:
        - attach new node with red link
        - 2-node → 3-node
        - 3-node → 4-node
        - split 4-node
        - pass red link up to parent and repeat
        - THEREFORE: no 4-nodes left! It's an LL 2-3 tree.

        """
        assert(self.left)
        assert(self.right)
        self.colour = self.colour.flip()
        self.left.colour = self.left.colour.flip()
        self.right.colour = self.right.colour.flip()
    def rotate_left(self) -> 'LLRBNode':
        """
        Either:
        - Takes a right-leaning 3-node (disallowed) and turns it into a
          left-leaning 3-node. We will want to run this when you insert a node
          (new ones red) to the right of a black node.
        - Or takes a left-right zig-zag double red sequence and turns it into a left-left double red sequence.
        Preserves both standard RB invariants.
        """
        assert(self.right)
        x = self.right
        self.right = x.left
        x.left = self
        x.colour = self.colour
        self.colour = Colour.RED
        return x
    def rotate_right(self) -> 'LLRBNode':
        """
        Takes a left-left double red sequence and turns it into a 4-node.
        Preserves both invariants"""
        assert(self.left)
        x = self.left
        self.left = x.right
        x.right = self
        x.colour = self.colour
        self.colour = Colour.RED
        return x

# cmp is gone in python 3
T = TypeVar('T')
def cmp(a: T, b: T) -> int:
    return int(a > b) - int(a < b)

def insert(h: Optional[LLRBNode], key: Any, debug=False):
    if h is None:
        return LLRBNode(key)
    # with flip_colours in this position, we have a 2-3-4 tree
    # if is_red(h.left) and is_red(h.right):
    #     h.flip_colours()
    c = cmp(key, h.item)
    if c < 0:
        h.left = insert(h.left, key, debug)
    # elif c == 0: overwrite value in map
    elif c > 0:
        h.right = insert(h.right, key, debug)
    h = fix_up_2_3(h)
    # with flip_colours in this position, we have a 2-3 tree
    return h

# based on the LLRB paper
# https://www.cs.princeton.edu/~rs/talks/LLRB/LLRB.pdf
# the slides have a different version of this somehow
def fix_up_2_3(h):
    if is_red(h.right) and not is_red(h.left):
        h = h.rotate_left()
    if is_red(h.left) and is_red(h.left.left):
        h = h.rotate_right()
    # with flip_colours in this position, we have a 2-3 tree
    if is_red(h.left) and is_red(h.right):
        h.flip_colours()
    return h

## deletion

# This is deletion for LLRB 2-3 Trees. It is based on the reverse of the
# approach used for insert in top-down 2-3-4 trees: we perform rotations and
# color flips on the way down the search path to ensure that the search does
# not end on a 2-node, so that we can just delete the node at the bottom.

# We use the method fix_up_2_3() to share the code for the color flip and rotations
# following the recursive calls in the insert() code. With fix-up(), we can
# leave right- leaning red links and unbalanced 4-nodes along the search path,
# secure that these conditions will be fixed on the way up the tree. (The
# approach is also effective 2-3-4 trees, but requires an extra rotation when
# the right node off the search path is a 4-node.)
#
# That's a bit hand wavy for 2-3-4 deletion; see:
# https://stackoverflow.com/questions/11336167/what-additional-rotation-is-required-for-deletion-from-a-top-down-2-3-4-left-lea

"""
Delete strategy (works for 2-3 and 2-3-4 trees)
- invariant: current node is not a 2-node
- introduce 4-nodes if necessary
- remove key from bottom
- eliminate 4-nodes on the way up

"""

def move_red_right(h):
    """
    Precondition: Invariant (either h or h.right is red)
    Precondition: h.left is black (we rotated away any LL 3-nodes)
    Precondition: h.right is a 2-node, i.e. h.right & h.right.left are BLACK
    Precondition: h.left & h.right are LL 2-3 trees, so both their right branches are black

        => h is RED, h.right is BLACK, h.right.left & h.right.right & h.left.right are BLACK

    When you flip h, h's parent is now either a 2- or LL3-node and h is now
    black. As for the stuff below h, 2 cases:
    - h.left.left was BLACK; you haven't created a double-red, you just made h a
      valid 4-node that h.right is part of.
      => h.right is now RED
      => h.right.right is still BLACK
    - h.left.left was RED (part of a 3-node); you have created a double-red
      left-left run. So,
      - rotate h right, making a right-right run from h;
      - then colour flip h, leaving h as the lower part of a RL3-node, and
        either a right-leaning 3-node or a 4-node on h.right.
      => h.right is BLACK
      => h.right.right is now RED

    Either way, you have only RL3-nodes and 4-nodes in the recursive stack to fix up;
    and you have the postcondition property that h.right is no longer a 2-node.

    Postcondition: either h.right or h.right.right is RED. Hence you have a new invariant with h=h.right
    Postcondition: h is not a 2-node
    Postcondition: h.right is either a RL 3-node or a 4-node
    Postcondition: h.left is a LL 2-3 tree

    (h.left.right doesn't matter, because we haven't touched it yet going down,
    so being in a left-leaning 2-3 tree it can only be black.)
    """
    h.flip_colours()
    if is_red(h.left.left):
        h = h.rotate_right()
        h.flip_colours()
    return h

def delete_max(h):
    """
    For 2-3 trees.

    Deleting the maximum:
     1. Search down the right spine of the tree (hence for the maximum).
     2. If search ends in a 3-node or 4-node: just turn it into a 2-node or 3-node,
     deleting the item.
     3. Removing a 2-node would destroy the black balance. So, transform the tree
     on the way down the search path, with the invariant "current node is not a
     2-node" hence if the search ends, you are not on a 2-node.

    Deleting the maximum continued:
        - Carry a red link down the right spine of the tree.
        - Invariant: either h or h.right is red (weaker: h is not a 2-node)
        - Implication: deletion is easy at bottom

        1. Rotate red links to the right
    """
    # rotate red links (left-leaning 3-nodes) to the right
    if is_red(h.left):
        h = h.rotate_right()
    # remove node on bottom level by returning None
    # h must be RED by invariant
    if h.right is None:
        return None
    # "borrow from sibling if necessary". Better: "push red down." This means "h.right is a 2-node, we
    # need to give it a red from somewhere; we now have h red and h.left/right black, so flip h and
    # you create a red on the left & the right, then make sure h.left.left isn't a double red by rotating right & flipping again if necessary"
    # being a 2-3 tree this if statement means "h.right is a 2-node"
    if not is_red(h.right) and not is_red(h.right.left):
        h = move_red_right(h)
    # The slides say h.left = deleteMax(h.left) but that's wrong
    h.right = delete_max(h.right)
    # here we fix the RL3-nodes (created by rotating LL3-notes and also move_red_right)
    return fix_up_2_3(h)

def move_red_left(h):
    """
    Precondition: delete_min's invariant (either h or h.left is RED)
    Precondition: h.left is BLACK and so too is h.left.left BLACK
    Precondition: h, h.left & h.right are LL 2-3 trees, so all of their rights are BLACK
        => Given, then: h.right.right and h.left.right BLACK

        => h is RED, h.left & h.right are BLACK, h.left.right & h.right.right & h.left.right are BLACK

    2 cases, depending on h.right.left:
    - h.right.left is black: now h.left is red, and so is h.right. h is now
      black and the top of a 4-node with black on all legs.
        => h.left is RED
    - h.right.left is red
        - after flip, you have a right-left zig-zag on the right, so rotate h.right right
        - h is now /\\ with an extra h.right.right double red
        - so rotate h into a /\\ with extra h.left.left double red
        - colour flip h again, leaving h red, h.left & h.right both BLACK, and h.left.left RED.
        - Hence h.left is now a left-leaning 3-node
        => h.left is BLACK
        => h.left.left is RED

    Postcondition:
        - Either h.left or h.left.left is red (you get the next invariant on h = h.left)

    """
    h.flip_colours()
    if is_red(h.right.left):
        h.right = h.right.rotate_right()
        h = h.rotate_left()
        h.flip_colours()
    return h

def delete_min(h, debug_hook = None):
    """
    Invariant: either h or h.left is RED (weaker: h is not a 2-node)
    Implication: deletion is easy at the bottom

    if h.left and h.left.left are both black, then h.left is a 2-node, so we
    need to borrow some red to make h.left not a 2-node. See move_red_left

    """
    debug_hook(h, "delete_min")
    # remove node on bottom by returning None instead of h
    if h.left is None:
        return None
    # borrow h's red link push red link down if necessary
    if not is_red(h.left) and not is_red(h.left.left):
        h = move_red_left(h)
    h.left = delete_min(h.left, debug_hook)
    return fix_up_2_3(h)

def min(h):
    while h.left:
        h = h.left
    return h

def delete(h, key, debug_hook = None):
    # you can't do cmp(key, h.item) only once. H changes.
    if key < h.item:
        if not h.left:
            # item not present
            return h
        if not is_red(h.left) and not is_red(h.left.left):
            if debug_hook:
                debug_hook(h, "moving red left")
            h = move_red_left(h)
        if debug_hook:
            debug_hook(h, "k < h, now deleting in h.left")
        h.left = delete(h.left, key, debug_hook)
    else:
        if is_red(h.left):
            h = h.rotate_right()

        if key == h.item and h.right is None:
            return None

        if not is_red(h.right) and not is_red(h.right.left):
            if debug_hook:
                debug_hook(h, "moving red right")
            h = move_red_right(h)

        if key == h.item:
            if debug_hook:
                debug_hook(h, "found k (1). h.item = min(h.right); h.right = delete_min(h.right)")
            m = min(h.right)
            h.item = m.item
            # h.value = m.value
            h.right = delete_min(h.right, debug_hook)
        else:
            if debug_hook:
                debug_hook(h, "k > h, now deleting in h.right")
            h.right = delete(h.right, key, debug_hook)

    if debug_hook:
        debug_hook(h, "pre fixup as stepping back out")
    h = fix_up_2_3(h)
    return h

class LLRB(RbTree):
    def __init__(self):
        self.root = None
        # self.size = 0

    def insert(self, key: Any, debug=False):
        if debug:
            print(self.graphviz("PreInsert", [str(key)]))
        self.root = insert(self.root, key, debug)
        self.root.colour = Colour.BLACK
        if debug:
            print(self.graphviz("PostInsert", [str(key)]))

    def delete_min(self):
        self.root = delete_min(self.root)
        if self.root:
            self.root.colour = Colour.BLACK

    def delete(self, key: Any, debug=False):
        if self.root:
            def debug_hook(h, why, only_h=True):
                if only_h:
                    tree = LLRB()
                    tree.root = h
                    print(tree.graphviz(f"Delete {key} (subtree): {why}", [str(h.item)]))
                else:
                    print(self.graphviz(f"Delete {key}: {why}", [str(h.item)]))
            if debug:
                print(self.graphviz("PreDelete", [str(key)]))
            hook = None
            if debug:
                hook = debug_hook
            self.root = delete(self.root, key, hook)
            if self.root:
                self.root.colour = Colour.BLACK
        if debug:
            print(self.graphviz("PostDelete", [str(key)]))

if __name__ == "__main__":
    import random

    tree = LLRB()
    vals = list(range(30))
    random.shuffle(vals)
    # some other weird case
    # vals = [12, 26, 24, 27, 23, 11, 3, 1, 15, 29, 14, 8, 2, 25, 13, 9, 28, 18, 6, 17, 0, 5, 22, 7, 19, 16, 10, 4, 21, 20]
    # 15 is the root node
    # vals = [29, 19, 15, 1, 3, 18, 20, 5, 22, 11, 23, 25, 13, 14, 17, 9, 27, 26, 4, 7, 16, 28, 8, 24, 2, 12, 21, 10, 0, 6]
    # vals = [10, 24, 19, 25, 27, 1, 7, 23, 28, 17, 16, 2, 26, 21, 15, 6, 20, 9, 11, 4, 12, 14, 5, 18, 29, 22, 3, 13, 8, 0]
    # vals = [17, 16, 6, 14, 20, 12, 26, 27, 8, 29, 7, 13, 24, 3, 9, 22, 15, 21, 2, 11, 1, 19, 28, 23, 5, 10, 4, 25, 18, 0]
    eprint(vals)
    j = 0
    for i in vals:
        tree.insert(i, debug= (j == 15))
        j += 1

    s = sorted(vals)
    assert(tree.to_list() == s)
    # assert(tree.max_depth() <= 2 * math.log2(len(vals) + 1))
    assert(tree.contains(15))
    tree.delete(15, debug=True)
    assert(not tree.contains(15))
    print(tree.graphviz234("Done"))
    # assert(not tree.contains(-100000))

