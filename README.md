# NFA--DFA


A Streamlit dashboard for visualizing and converting ε-NFA/NFA to DFA, with support for Excel uploads and LaTeX export.

## System Requirements

- Python 3.8+
- [Graphviz system binaries](https://graphviz.gitlab.io/download/) (required for diagram rendering)

## Features

- Upload NFA definitions from Excel or enter them manually
- Visualize NFA and DFA state diagrams (Graphviz)
- View and export transition tables (including LaTeX format)
- Download SVG diagrams

## Requirements

- Python 3.8+
- See [requirements.txt](requirements.txt) for dependencies

> **Note:** The Python `graphviz` package requires the Graphviz system binaries.  
> Install them via your package manager, e.g.:
> - Ubuntu: `sudo apt-get install graphviz`
> - macOS: `brew install graphviz`
> - Windows: Download from [Graphviz website](https://graphviz.gitlab.io/download/)

If required, install additional system packages listed in `packages.txt`:

```sh
xargs -a packages.txt sudo apt-get install -y
```

## Installation

```sh
pip install -r requirements.txt
```

See above for installing Graphviz system binaries if you have not already.

## Usage

Run the Streamlit app:

```sh
streamlit run NFA_DFA.py
```

## Input Formats

### Excel Upload

Your Excel file should have columns: `State`, `Input`, `Next_State`, and optionally `Start_State`, `Final_State`.

### Manual Input

- Enter states, alphabet, start/final states in the sidebar.
- Specify transitions for each state and symbol (including ε) in the sidebar.

## Output

- Interactive state diagrams for NFA and DFA
- Transition tables (with LaTeX export)
- Downloadable SVG diagrams

## Example

See [example_nfa.xlsx](example_nfa.xlsx) for a sample input file.

## Troubleshooting

- If diagrams do not render, ensure Graphviz system binaries are installed and available in your PATH.
- For Streamlit issues, see [Streamlit documentation](https://docs.streamlit.io/).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT License