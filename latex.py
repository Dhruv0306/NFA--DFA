# nfa_dfa_latex.py
"""
LaTeX table generation functions for NFA/DFA tables.
"""

def df_to_latex_matrix_phi(states, alphabet, transitions, start_state, final_states, caption="Table"):
    latex = "\\begin{table}[H]\n"
    latex += "    \\centering\n"
    latex += "    \\begin{tabular}{|" + "c|"*(len(alphabet)+1) + "}\n"
    latex += "    \\hline\n"
    latex += "State & " + " & ".join(f"$\\epsilon$" if a=="ε" else a for a in alphabet) + " \\ \\hline\n"
    for s in states:
        row = s
        if s == start_state:
            row = f"$\\rightarrow$ {row}"
        if s in final_states:
            row = f"*{row}"
        row += " & "
        row += " & ".join(",".join(sorted(transitions.get((s, a), set()))) if (s, a) in transitions else "" for a in alphabet)
        row += " \\ \\hline\n"
        latex += row
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
    latex += "State & " + " & ".join(header_symbols) + " \\ \\hline\n"
    for S in states:
        S_lbl = "".join(sorted(S)) if isinstance(S, frozenset) else str(S)
        row = S_lbl
        if S == start_state:
            row = f"$\\rightarrow$ {row}"
        if S in final_states:
            row = f"*{row}"
        row += " & "
        row += " & ".join("".join(sorted(transitions.get((S, a), set()))) if (S, a) in transitions and isinstance(transitions.get((S, a)), set) else str(transitions.get((S, a), "")) for a in header_symbols)
        row += " \\ \\hline\n"
        latex += row
    latex += "    \\end{tabular}\n"
    latex += f"    \\caption{{{caption}}}\n"
    latex += "\\end{table}"
    return latex
