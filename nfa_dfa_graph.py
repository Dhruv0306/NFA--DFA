# nfa_dfa_graph.py
"""
Graphviz drawing functions for NFA/DFA diagrams.
"""
import graphviz

def draw_state_node(dot, state, is_start=False, is_final=False, is_dead=False, color="black"):
    shape = "doublecircle" if is_final else "circle"
    if is_start:
        dot.node(state, shape=shape, color=color, style="bold")
    elif is_final:
        dot.node(state, shape=shape, color=color, peripheries="2")
    elif is_dead:
        dot.node(state, shape=shape, color="gray", style="dashed")
    else:
        dot.node(state, shape=shape, color=color)

def draw_nfa_graph(states, alphabet, nfa_no_e, start_state, final_states, color="black"):
    dot = graphviz.Digraph()
    dot.attr(rankdir="LR")
    dot.node("", shape="none")
    for s in states:
        draw_state_node(dot, s, is_start=(s==start_state), is_final=(s in final_states))
    dot.edge("", start_state, color=color)
    self_loops = {}
    for (src, a), dsts in nfa_no_e.items():
        if src in final_states and src in dsts:
            self_loops.setdefault(src, []).append(a)
        else:
            for dst in dsts:
                dot.edge(src, dst, label=a, color=color)
    for state, inputs in self_loops.items():
        dot.edge(state, state, label=",".join(inputs), color=color)
    return dot

def draw_dfa_graph(dfa_states, alphabet, dfa_trans, dfa_start, dfa_finals, color="black"):
    dot = graphviz.Digraph()
    dot.attr(rankdir="LR")
    dot.node("", shape="none")
    def label_of(S):
        if isinstance(S, frozenset):
            return "".join(sorted(S))
        return str(S)
    dead_state = None
    for S in dfa_states:
        lbl = label_of(S)
        is_start = (S == dfa_start)
        is_final = (S in dfa_finals)
        is_dead = (lbl == "q_D")
        if is_dead:
            dead_state = S
        draw_state_node(dot, lbl, is_start=is_start, is_final=is_final, is_dead=is_dead, color=color)
    dot.edge("", label_of(dfa_start), color=color)
    if dead_state:
        lbl = label_of(dead_state)
        dot.edge(lbl, lbl, label=",".join(alphabet), color="gray")
    for (src, a), dst in dfa_trans.items():
        src_lbl = label_of(src)
        dst_lbl = label_of(dst)
        if src_lbl == "q_D" and dst_lbl == "q_D":
            continue
        dot.edge(src_lbl, dst_lbl, label=a, color=color)
    return dot
