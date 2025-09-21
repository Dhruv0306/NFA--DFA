# Codacy analysis required after file edit (see .github/instructions/codacy.instructions.md)
# nfa_dfa_core.py
"""
Core logic for NFA→DFA conversion and minimization.
"""

def parse_list(raw: str):
    return [x.strip() for x in raw.split(",") if x.strip()]

# ---------- NFA → DFA functions ----------
def epsilon_closure_of(state, enfa):
    stack = [state]
    closure = {state}
    while stack:
        s = stack.pop()
        for nxt in enfa.get((s, "ε"), set()):
            if nxt not in closure:
                closure.add(nxt)
                stack.append(nxt)
    return closure


def remove_epsilon(states, alphabet, enfa, start_state, final_states):
    closures = {s: epsilon_closure_of(s, enfa) for s in states}
    nfa_no_e = {}
    nfa_finals = set()
    for s in states:
        if any(f in closures[s] for f in final_states):
            nfa_finals.add(s)
        for a in alphabet:
            dests = set()
            for t in closures[s]:
                dests.update(enfa.get((t, a), set()))
            # Closure of all reachable states
            closure_dests = set()
            for d in dests:
                closure_dests.update(closures[d])
            if closure_dests:
                nfa_no_e[(s, a)] = closure_dests
    return closures, nfa_no_e, nfa_finals


def nfa_to_dfa(states, alphabet, nfa_no_e, start_state, final_states):
    dfa_start = frozenset([start_state])
    dfa_states = [dfa_start]
    unmarked = [dfa_start]
    dfa_trans = {}
    dfa_finals = set()
    dead_state = frozenset(["q_D"])
    has_dead_state = False
    # Only use non-epsilon symbols for DFA transitions
    dfa_alphabet = [a for a in alphabet if a != "ε"]
    while unmarked:
        S = unmarked.pop()
        for a in dfa_alphabet:
            dest = set()
            for s in S:
                dest.update(nfa_no_e.get((s, a), set()))
            dest_frozen = frozenset(dest)
            if dest:
                if dest_frozen not in dfa_states:
                    dfa_states.append(dest_frozen)
                    unmarked.append(dest_frozen)
                dfa_trans[(S, a)] = dest_frozen
            else:
                dfa_trans[(S, a)] = dead_state
                has_dead_state = True
    # Add dead state only if needed
    if has_dead_state:
        dfa_states.append(dead_state)
        for a in dfa_alphabet:
            dfa_trans[(dead_state, a)] = dead_state
    for S in dfa_states:
        if any(s in final_states for s in S):
            dfa_finals.add(S)
    return dfa_states, dfa_trans, dfa_start, dfa_finals

# ---------- DFA Minimization ----------
def minimize_dfa(states, alphabet, transitions, start_state, final_states):
    alphabet = [a for a in alphabet if a != "ε"]
    states = list(states)
    finals = set(final_states)
    non_finals = set(states) - finals
    partitions = []
    if finals:
        partitions.append(finals)
    if non_finals:
        partitions.append(non_finals)
    def get_partition(state, partitions):
        for idx, group in enumerate(partitions):
            if state in group:
                return idx
        return None
    changed = True
    while changed:
        changed = False
        new_partitions = []
        for group in partitions:
            splitter = {}
            for s in group:
                key = tuple(get_partition(transitions.get((s, a), None), partitions) for a in alphabet)
                splitter.setdefault(key, set()).add(s)
            if len(splitter) > 1:
                changed = True
                new_partitions.extend(splitter.values())
            else:
                new_partitions.append(group)
        partitions = new_partitions
    group_name_map = {}
    state_map = {}
    def state_to_label(s):
        if isinstance(s, frozenset):
            return "".join(sorted(s))
        return str(s)
    for group in partitions:
        if len(group) == 1:
            group_label = state_to_label(next(iter(group)))
        else:
            group_label = "{" + ",".join(sorted(state_to_label(s) for s in group)) + "}"
        for s in group:
            state_map[s] = group_label
        group_name_map[group_label] = group
    min_states = set(group_name_map.keys())
    min_start = state_map[start_state]
    min_finals = set(state_map[s] for s in finals if s in state_map)
    min_trans = {}
    for s in min_states:
        group = group_name_map[s]
        orig = next(iter(group))
        for a in alphabet:
            dst = transitions.get((orig, a), None)
            if dst is not None:
                min_trans[(s, a)] = state_map.get(dst, dst)
    return min_states, alphabet, min_trans, min_start, min_finals
