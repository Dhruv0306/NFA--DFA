

import streamlit as st
import pandas as pd
import graphviz
from nfa_dfa_core import remove_epsilon, nfa_to_dfa, minimize_dfa
from nfa_dfa_graph import draw_nfa_graph, draw_dfa_graph
from nfa_dfa_latex import df_to_latex_matrix_phi, dfa_to_latex
from utils import parse_list, df_to_excel_bytes

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
        # Accept frozenset or set of frozenset (minimized DFA)
        if isinstance(S, (set, frozenset)):
            # If S is a set with one frozenset inside, extract it
            if len(S) == 1 and isinstance(next(iter(S)), frozenset):
                S = next(iter(S))
            return ", ".join(sorted(str(x) for x in S))
        return str(S)
    
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
        # If dst is a set with one frozenset, extract it
        if isinstance(dst, set) and len(dst) == 1 and isinstance(next(iter(dst)), frozenset):
            dst = next(iter(dst))
        dot.edge(label_of(src), label_of(dst), label=a, color=color)
    
    return dot

# ---------- LaTeX functions ----------
def df_to_latex_matrix_phi(states, alphabet, transitions, start_state, final_states, caption="Table"):
    latex = "\\begin{table}[H]\n"
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
    latex = "\\begin{table}[H]\n"
    latex += "    \\centering\n"
    latex += "    \\begin{tabular}{|" + "c|"*(len(alphabet)+1) + "}\n"
    latex += "    \\hline\n"
    header_symbols = [a for a in alphabet if a != "ε"]
    latex += "State & " + " & ".join(header_symbols) + " \\\\ \\hline\n"

    for S in states:
        S_lbl = ", ".join(sorted(S)) if isinstance(S, (set, frozenset)) else str(S)
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
                # If nxt is a set with one frozenset, extract it
                if isinstance(nxt, set) and len(nxt) == 1 and isinstance(next(iter(nxt)), frozenset):
                    nxt = next(iter(nxt))
                dst = ", ".join(sorted(str(x) for x in nxt))
                row_entries.append(dst)
            else:
                row_entries.append(r"$\phi$")
        latex += S_lbl + " & " + " & ".join(row_entries) + " \\ \\hline\n"

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
    # Assume first column is 'State', rest are input symbols
    nfa_states = [str(x).replace("→", "").replace("*", "") for x in df['State']]
    alphabet = [str(col) for col in df.columns if col != "State"]
    start_state = None
    final_states = []
    nfa_transitions = {}

    for idx, row in df.iterrows():
        state_raw = str(row['State'])
        state = state_raw.replace("→", "").replace("*", "")
        if "→" in state_raw:
            start_state = state
        if "*" in state_raw:
            final_states.append(state)
        for a in alphabet:
            cell = str(row[a]).strip()
            if cell and cell != "φ" and cell.lower() != "nan":
                next_states = [s.strip() for s in cell.split(",") if s.strip()]
                nfa_transitions[(state, a)] = set(next_states)
    # Fallback if no start state marked
    if not start_state:
        start_state = nfa_states[0]
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


# ---------- Minimized DFA ----------
min_states, min_alphabet, min_trans, min_start, min_finals = minimize_dfa(
    dfa_states, alphabet, dfa_trans, dfa_start, dfa_finals
)


# ----- NFA -----
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

nfa_df = pd.DataFrame(nfa_table_data)
st.dataframe(nfa_df)

# --- NFA Excel Download ---
import io
from io import BytesIO

def df_to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button(
    label="Download NFA Table (Excel)",
    data=df_to_excel_bytes(nfa_df),
    file_name="nfa_table.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.subheader("NFA Table LaTeX")
st.code(df_to_latex_matrix_phi(nfa_states, alphabet + ["ε"], nfa_transitions, start_state, nfa_finals, caption="Original NFA Transition Table"), language="latex")

# ----- DFA -----
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

dfa_df = pd.DataFrame(dfa_table_data)
st.dataframe(dfa_df)

# --- DFA Excel Download ---
st.download_button(
    label="Download DFA Table (Excel)",
    data=df_to_excel_bytes(dfa_df),
    file_name="dfa_table.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.subheader("DFA Table LaTeX")
st.code(dfa_to_latex(dfa_states, alphabet, dfa_trans, dfa_start, dfa_finals, caption="Original DFA Transition Table"), language="latex")

# ----- Minimized DFA -----

st.subheader("Minimized DFA State Diagram")
min_dot = draw_dfa_graph(min_states, min_alphabet, min_trans, min_start, min_finals, color="black")
st.graphviz_chart(min_dot)
st.download_button("Download Minimized DFA Diagram (SVG)", data=min_dot.pipe(format="svg"), file_name="min_dfa.svg")

st.markdown("### Minimized DFA Transition Table")
min_table_data = []
for S in min_states:
    S_lbl = str(S)
    if S == min_start:
        S_lbl = "→" + S_lbl
    if S in min_finals:
        S_lbl += "*"
    row_entries = {}
    for a in min_alphabet:
        nxt = min_trans.get((S,a))
        if nxt:
            # nxt is a set with one label string
            dst_label = next(iter(nxt))
            row_entries[a] = dst_label
        else:
            row_entries[a] = "φ"
    min_table_data.append({"State": S_lbl, **row_entries})

min_df = pd.DataFrame(min_table_data)
st.dataframe(min_df)

# --- Minimized DFA Excel Download ---
st.download_button(
    label="Download Minimized DFA Table (Excel)",
    data=df_to_excel_bytes(min_df),
    file_name="minimized_dfa_table.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.subheader("Minimized DFA Table LaTeX")
st.code(dfa_to_latex(min_states, min_alphabet, min_trans, min_start, min_finals, caption="Minimized DFA Transition Table"), language="latex")
