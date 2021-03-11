void RBinsert1(
        RBtree* T,         // -> red–black tree
        struct RBnode* P,  // -> parent node of N (may be NULL)
        struct RBnode* N,  // -> node to be inserted
        byte dir)          // side of P on which to insert N (∈ { LEFT, RIGHT })
{
    struct RBnode* G;  // -> parent node of P
    struct RBnode* U;  // -> uncle of N

    N->color = RED;
    N->left  = NIL;
    N->right = NIL;
    N->parent = P;
    if (P == NULL) {   // There is no parent
        T->root = N;     // N is the new root of the tree T.
        return; // insertion complete
    }
    P->child[dir] = N; // insert N as dir-child of P
    // fall through to the loop
    // start of the (do while)-loop:
    do {
        if (P->color == BLACK) {
            // Case_I3 (P black):
            return; // insertion complete
        }
        // From now on P is red.
        if ((G = GetParent(P)) == NULL) 
            goto Case_I6; // P red and root
        // else: P red and G!=NULL.
        if (((U = GetUncle(N)) == NIL) || U->color == BLACK) // considered black
            goto Case_I45; // P red && U black
        // Case_I1 (P+U red):
        P->color = BLACK;
        U->color = BLACK;
        G->color = RED;
        N = G; // new current node
        // iterate 1 black level (= 2 tree levels) higher
    } while ((P = N->parent) != NULL); // end of (do while)-loop
    // fall through to Case_I2
    // Case_I2 (P == NULL):
    return; // insertion complete

Case_I45: // P red && U black:
    dir = childDir(P); // the side of parent G on which node P is located
    if (N == P->child[1-dir]) {
        // Case_I4 (P red && U black && N inner grandchild of G):
        RotateDir(P,dir); // P is never the root
        N = P; // new current node
        P = G->child[dir]; // new parent of N
        // fall through to Case_I5
    }

    // Case_I5 (P red && U black && N outer grandchild of G):
    P->color = BLACK;
    G->color = RED;
    RotateDirRoot(T,G,1-dir); // G may be the root
    return; // insertion complete

Case_I6: // P is the root and red:
    P->color = BLACK;
    return; // insertion complete

} // end of RBinsert1

