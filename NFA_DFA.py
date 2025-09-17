import streamlit as st
import pandas as pd
import graphviz

# ---------- Utilities ----------
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
            if a == "ε":  # skip epsilon in DFA
                continue
            move = set()
            for c in closures[s]:
                move |= enfa.get((c, a), set())
            if move:
                dest = set()
                for m in move:
                    dest |= closures[m]
                nfa_no_e[(s, a)] = dest
            elif s in final_states:
                # Final state with no transition leads to self-loop
                nfa_no_e[(s, a)] = {s}
    return closures, nfa_no_e, nfa_finals

def nfa_to_dfa(states, alphabet, nfa_no_e, start_state, final_states):
    dfa_start = frozenset([start_state])
    dfa_states = [dfa_start]
    unmarked = [dfa_start]
    dfa_trans = {}
    dfa_finals = set()
    dead_state = frozenset(["q_D"])
    has_dead_state = False
    
    while unmarked:
        S = unmarked.pop()
        for a in alphabet:
            if a == "ε":
                continue
            nxt = set()
            for s in S:
                nxt |= nfa_no_e.get((s, a), set())
            if nxt:
                nxt_f = frozenset(nxt)
                dfa_trans[(S, a)] = nxt_f
                if nxt_f not in dfa_states:
                    dfa_states.append(nxt_f)
                    unmarked.append(nxt_f)
            else:
                dfa_trans[(S, a)] = dead_state
                has_dead_state = True
    
    # Add dead state if needed
    if has_dead_state:
        dfa_states.append(dead_state)
        # Dead state transitions to itself for all inputs
        for a in alphabet:
            if a != "ε":
                dfa_trans[(dead_state, a)] = dead_state
    
    for S in dfa_states:
        if any(s in final_states for s in S):
            dfa_finals.add(S)
    return dfa_states, dfa_trans, dfa_start, dfa_finals

# ---------- Graphviz ----------
def draw_state_node(dot, state, is_start=False, is_final=False, is_dead=False, color="black"):
    shape = "doublecircle" if is_final else "circle"
    if is_start:
        dot.node(state, state, shape=shape, color="blue", fillcolor="blue", style="filled", fontcolor="white", fontname="Arial Bold")
    elif is_final:
        dot.node(state, state, shape=shape, color="green", fillcolor="green", style="filled", fontcolor="black", fontname="Arial Bold")
    elif is_dead:
        dot.node(state, state, shape=shape, color="red", fillcolor="red", style="filled", fontcolor="white", fontname="Arial Bold")
    else:
        dot.node(state, state, shape=shape, color=color, fontcolor=color)

def draw_nfa_graph(states, alphabet, nfa_no_e, start_state, final_states, color="black"):
    dot = graphviz.Digraph()
    dot.attr(rankdir="LR")
    dot.node("", shape="none")
    for s in states:
        draw_state_node(dot, s, is_start=(s==start_state), is_final=(s in final_states), color=color)
    dot.edge("", start_state, color=color)
    
    # Group self-loops for final states
    self_loops = {}
    for (src, a), dsts in nfa_no_e.items():
        if src in final_states and dsts == {src}:
            if src not in self_loops:
                self_loops[src] = []
            self_loops[src].append(a)
        else:
            for d in sorted(dsts):
                dot.edge(src, d, label=a, color=color)
    
    # Draw combined self-loops for final states
    for state, inputs in self_loops.items():
        dot.edge(state, state, label=",".join(inputs), color=color)
    
    return dot

def draw_dfa_graph(dfa_states, alphabet, dfa_trans, dfa_start, dfa_finals, color="black"):
    dot = graphviz.Digraph()
    dot.attr(rankdir="LR")
    dot.node("", shape="none")
    def label_of(S): 
        return "".join(sorted(S))
    
    dead_state = None
    for S in dfa_states:
        is_dead = ("q_D" in S and len(S) == 1)
        if is_dead:
            dead_state = S
        draw_state_node(dot, label_of(S), is_start=(S==dfa_start), is_final=(S in dfa_finals), is_dead=is_dead, color=color)
    
    dot.edge("", label_of(dfa_start), color=color)
    
    # Handle dead state self-loop separately
    if dead_state:
        dead_inputs = [a for a in alphabet if a != "ε" and dfa_trans.get((dead_state, a)) == dead_state]
        if dead_inputs:
            dot.edge(label_of(dead_state), label_of(dead_state), label=",".join(dead_inputs), color=color)
    
    # Draw other transitions
    for (src, a), dst in dfa_trans.items():
        if src == dead_state and dst == dead_state:
            continue  # Skip dead state self-loops, already handled
        dot.edge(label_of(src), label_of(dst), label=a, color=color)
    
    return dot

# ---------- LaTeX functions ----------
def df_to_latex_matrix_phi(states, alphabet, transitions, start_state, final_states, caption="Table"):
    latex = "\\begin{table}[h]\n"
    latex += "    \\centering\n"
    latex += "    \\begin{tabular}{|" + "c|"*(len(alphabet)+1) + "}\n"
    latex += "    \\hline\n"
    latex += "State & " + " & ".join(f"$\\epsilon$" if a=="ε" else a for a in alphabet) + " \\\\ \\hline\n"

    for s in states:
        row_label = s
        if s == start_state:
            row_label = "→" + row_label
        if s in final_states:
            row_label += "*"
        row_entries = []
        for a in alphabet:
            nxt = transitions.get((s,a), set())
            if nxt:
                row_entries.append(",".join(sorted(nxt)) if len(nxt)>1 else next(iter(nxt)))
            else:
                row_entries.append(r"$\phi$")
        latex += row_label + " & " + " & ".join(row_entries) + " \\\\ \\hline\n"

    latex += "    \\end{tabular}\n"
    latex += f"    \\caption{{{caption}}}\n"
    latex += "\\end{table}"
    return latex

def dfa_to_latex(states, alphabet, transitions, start_state, final_states, caption="DFA Table"):
    latex = "\\begin{table}[h]\n"
    latex += "    \\centering\n"
    latex += "    \\begin{tabular}{|" + "c|"*(len(alphabet)+1) + "}\n"
    latex += "    \\hline\n"
    header_symbols = [a for a in alphabet if a != "ε"]
    latex += "State & " + " & ".join(header_symbols) + " \\\\ \\hline\n"

    for S in states:
        S_lbl = "".join(sorted(S))
        if S == start_state:
            S_lbl = "→" + S_lbl
        if S in final_states:
            S_lbl += "*"
        row_entries = []
        for a in alphabet:
            if a == "ε":
                continue
            nxt = transitions.get((S,a))
            if nxt:
                dst = "".join(sorted(nxt))
                row_entries.append(dst)
            else:
                row_entries.append(r"$\phi$")
        latex += S_lbl + " & " + " & ".join(row_entries) + " \\\\ \\hline\n"

    latex += "    \\end{tabular}\n"
    latex += f"    \\caption{{{caption}}}\n"
    latex += "\\end{table}"
    return latex

# ---------- Streamlit ----------
st.set_page_config(page_title="NFA → DFA Dashboard", layout="wide")
st.title("ε-NFA / NFA → DFA Dashboard")

# ---------- Sidebar ----------
st.sidebar.header("📥 Excel Upload")
uploaded_file = st.sidebar.file_uploader("Drag and drop NFA Excel file", type=["xlsx"])

st.sidebar.header("Manual Input")
manual_states = st.sidebar.text_input("States (comma separated)", "q0,q1")
manual_alphabet = st.sidebar.text_input("Alphabet (comma separated)", "a,b")
manual_start = st.sidebar.text_input("Start State", "q0")
manual_final = st.sidebar.text_input("Final States (comma separated)", "q1")

# ---------- Parse Inputs ----------
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    nfa_states = [str(x) for x in df['State'].unique()]
    alphabet = [str(x) for x in df['Input'].unique()]
    start_state = str(df['Start_State'].dropna().iloc[0]) if 'Start_State' in df.columns else nfa_states[0]
    final_states = [str(x) for x in df['Final_State'].dropna()]
    
    # Add final states to nfa_states if not present
    for fs in final_states:
        if fs not in nfa_states:
            nfa_states.append(fs)
    
    nfa_transitions = {}
    for _, row in df.iterrows():
        key = (str(row['State']), str(row['Input']))
        if key not in nfa_transitions:
            nfa_transitions[key] = set()
        nfa_transitions[key].add(str(row['Next_State']))
else:
    nfa_states = parse_list(manual_states)
    alphabet = parse_list(manual_alphabet)
    start_state = manual_start.strip()
    final_states = parse_list(manual_final)
    st.sidebar.markdown("#### Transitions")
    nfa_transitions = {}
    for state in nfa_states:
        for sym in alphabet + ["ε"]:  # Include epsilon
            next_states = st.sidebar.text_input(f"δ({state}, {sym}) (comma separated)", "").strip()
            if next_states:
                nfa_transitions[(state, sym)] = set(ns.strip() for ns in next_states.split(","))

# ---------- Validation ----------
error_msg = None
if start_state not in nfa_states:
    error_msg = f"❌ Start state `{start_state}` is not in states!"
elif not set(final_states).issubset(set(nfa_states)):
    error_msg = "❌ Some final states are not in the set of states!"
elif any(dst not in nfa_states for dsts in nfa_transitions.values() for dst in dsts):
    error_msg = "❌ Some transitions point to states not in the state set!"
if error_msg:
    st.error(error_msg)
    st.stop()

# ---------- NFA → DFA ----------
closures, nfa_no_e, nfa_finals = remove_epsilon(nfa_states, alphabet, nfa_transitions, start_state, final_states)
dfa_states, dfa_trans, dfa_start, dfa_finals = nfa_to_dfa(nfa_states, alphabet, nfa_no_e, start_state, nfa_finals)

# ---------- Display ----------
col1, col2 = st.columns(2)

# ----- NFA -----
with col1:
    st.subheader("NFA State Diagram")
    nfa_dot = draw_nfa_graph(nfa_states, alphabet, nfa_transitions, start_state, nfa_finals, color="black")
    st.graphviz_chart(nfa_dot)
    st.download_button("Download NFA Diagram (SVG)", data=nfa_dot.pipe(format="svg"), file_name="nfa.svg")

    st.markdown("### NFA Transition Table")
    nfa_table_data = []
    for s in nfa_states:
        row_label = s
        if s == start_state:
            row_label = "→" + row_label
        if s in nfa_finals:
            row_label += "*"
        row_entries = {}
        for a in alphabet + ["ε"]:
            nxt = nfa_transitions.get((s,a), set())
            row_entries[a] = ",".join(sorted(nxt)) if nxt else "φ"
        nfa_table_data.append({"State": row_label, **row_entries})
    st.dataframe(pd.DataFrame(nfa_table_data))
    
    st.subheader("NFA Table LaTeX")
    st.code(df_to_latex_matrix_phi(nfa_states, alphabet + ["ε"], nfa_transitions, start_state, nfa_finals, caption="Original NFA Transition Table"), language="latex")

# ----- DFA -----
with col2:
    st.subheader("DFA State Diagram")
    dfa_dot = draw_dfa_graph(dfa_states, alphabet, dfa_trans, dfa_start, dfa_finals, color="black")
    st.graphviz_chart(dfa_dot)
    st.download_button("Download DFA Diagram (SVG)", data=dfa_dot.pipe(format="svg"), file_name="dfa.svg")

    st.markdown("### DFA Transition Table")
    dfa_table_data = []
    for S in dfa_states:
        S_lbl = "".join(sorted(S))
        if S == dfa_start:
            S_lbl = "→" + S_lbl
        if S in dfa_finals:
            S_lbl += "*"
        row_entries = {}
        for a in alphabet:
            if a == "ε":
                continue
            nxt = dfa_trans.get((S,a))
            row_entries[a] = "".join(sorted(nxt)) if nxt else "φ"
        dfa_table_data.append({"State": S_lbl, **row_entries})
    st.dataframe(pd.DataFrame(dfa_table_data))
    
    st.subheader("DFA Table LaTeX")
    st.code(dfa_to_latex(dfa_states, alphabet, dfa_trans, dfa_start, dfa_finals, caption="Original DFA Transition Table"), language="latex")
