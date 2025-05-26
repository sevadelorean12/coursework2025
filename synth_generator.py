import random
import subprocess
import os
import pdflatex



with open('russian.txt', encoding='windows-1251') as f:
    russian_words = [line.strip() for line in f if line.strip()]

def random_russian_text(length):
    text = rf'\text{{'
    for _ in range(length):
        text += rf'{random.choice(russian_words)} '
    text += '}'
    return text

os.makedirs("output", exist_ok=True)

singletons = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    '1', '2', '3', '4', '5', '6', '7', '8', '9',
    '\\alpha', '\\beta', '\\gamma', '\\delta', '\\epsilon', '\\varepsilon', '\\zeta', '\\eta' '\\theta', '\\iota', '\\kappa', '\\lambda',
    '\\mu', '\\nu', '\\xi', '\\o', '\\pi', '\\rho', '\\sigma', '\\tau', '\\phi', '\\varphi', '\\chi', '\\psi', '\\omega', '\\Gamma', '\\Delta',
    '\\Theta', '\\Lambda', '\\Pi', '\\Sigma', '\\Phi', '\\Psi', '\\Omega'
]

one_ops = [
    r'\sqrt{#}', r'\sqrt[#]{#}',
    r'\sin{#}', r'\cos{#}', r'\tan{#}',
    r'\arcsin{#}', r'\arccos{#}', r'\arctan{#}',
    r'\ln{#}', r'\log{#}', r'\exp{#}',
    r'\vec{#}', r'\hat{#}', r'\bar{#}', r'\tilde{#}',
    r'\left|#\right|', r'\left\lceil #\right\rceil', r'\left\lfloor #\right\rfloor',
]


two_ops = [
    r'# + #', r'# - #', r'# \cdot #', r'# \times #', r'# \div #', r'# / #',
    r'# = #', r'# \approx #', r'# \equiv #', r'# \neq #',
    r'# < #', r'# > #', r'# \leq #', r'# \geq #',
    r'# \cup #', r'# \cap #', r'# \setminus #',
    r'# \in #', r'# \notin #', r'# \subset #', r'# \subseteq #', r'# \supseteq #',
    r'# \to #', r'# \mapsto #', r'# \Rightarrow #', r'# \iff #',
    r'\frac{#}{#}'
]


three_ops = [
    r'\sum_{#}^{#} #',
    r'\prod_{#}^{#} #',
    r'\int_{#}^{#} #',
    r'\lim_{# \to #} #',
    r'\limsup_{# \to #} #',
    r'\liminf_{# \to #} #',
    r'\bigcup_{#}^{#} #', r'\bigcap_{#}^{#} #',
    r'\left[ \sum_{#=1}^{#} # \right]'
]


weights = {
    'singleton': 0.6,
    'one_op': 0.1,
    'two_op': 0.25,
    'three_op': 0.05
}

def generate_expression():
    expr = '#'
    while any(token == '#' for token in expr):
        index = expr.index('#')
        r = random.random()
        if r < weights['singleton']:
            replacement = random.choice(singletons)
        elif r < weights['singleton'] + weights['one_op']:
            replacement = random.choice(one_ops)
        elif r < weights['singleton'] + weights['one_op'] + weights['two_op']:
            replacement = random.choice(two_ops)
        else:
            replacement = random.choice(three_ops)
        expr = expr[:index] + replacement + expr[index+1:]
    return ''.join(expr)


header = r"""
\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T2A]{fontenc}
\usepackage[russian]{babel}
\usepackage{amsmath,amssymb}
\usepackage{geometry}
\geometry{margin=1in}
\begin{document}
"""

footer = r"\end{document}"

body = ""


if __name__ == "__main__":
    for file_id in range(10):
        body = ""
        for _ in range(10):
            body += f"${generate_expression()}$\n"
            body += r"\par\vspace{4mm}" + '\n'
            body += random_russian_text(5) + '\n'
            body += r"\par\vspace{4mm}" + '\n'

        tex_code = header + '\n' + body + '\n' + footer
        base = f"output/page_{file_id:04d}"

        with open(f"{base}.tex", "w", encoding="utf-8") as f:
            f.write(tex_code)
        with open(f"{base}.txt", "w", encoding="utf-8") as f:
            f.write(tex_code)

        subprocess.run([
            "pdflatex",
            "-interaction=nonstopmode",
            f"page_{file_id:04d}.tex"
        ], cwd="output")

        subprocess.run([
            "magick",
            "-density", "300",
            f"page_{file_id:04d}.pdf",
            "-quality", "90",
            "-background", "white",
            "-alpha", "remove",
            "-alpha", "off",
            f"page_{file_id:04d}.png"
        ], cwd="output")

        for ext in [".aux", ".log", ".pdf", ".tex"]:
            try:
                os.remove(f"{base}{ext}")
            except FileNotFoundError:
                pass
