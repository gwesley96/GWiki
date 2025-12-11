#!/bin/bash
# Generate comprehensive TikZ test suite (tests 07-20)

NOTES_DIR="notes"

# Test 07: Multiline
cat > "$NOTES_DIR/tikz test 07 multiline.tex" << 'EOF'
\documentclass{gwiki}
\usepackage{gwiki-links}
\usepackage{tz}

\Title{tikz test 07 multiline}
\Tags{tikz, visualization, test}

\begin{document}
\NoteHeader

Multi-line path styles: \texttt{tripleline}, \texttt{quadrupleline}, \texttt{double strand}. \allformats{tikz test 07 multiline}

Navigation: \wref{tikz test 06 string diagrams} (previous) | \wref{tikz test 08 knots} (next)

\section*{Triple Line Style}

\begin{center}
\tz{
  \draw[tripleline=[thick,blue] in [very thick,white] in [thick,red]] (0,0) -- (4,0);
  \node[below] at (2,-0.5) {Blue-White-Red triple};
}
\end{center}

\subsection*{Curved Triple Line}

\begin{center}
\tz{
  \draw[tripleline=[thick,strA] in [ultra thick,white] in [thick,strB]]
    (0,0) to[bend left=45] (4,0);
}
\end{center}

\section*{Quadruple Line Style}

\begin{center}
\tz{
  \draw[quadrupleline=[thin,black] in [thick,yellow] in [ultra thick,white] in [very thick,red]]
    (0,0) .. controls (1,1) and (3,-1) .. (4,0);
}
\end{center}

\subsection*{Double Strand}

\begin{center}
\tz{
  \draw[double strand=3pt, colA] (0,0) -- (3,0);
  \draw[double strand=5pt, colB] (0,0.7) -- (3,0.7);
  \draw[double strand=7pt, colC] (0,1.4) -- (3,1.4);
}
\end{center}

\subsection*{Multi-strand Diagram}

\begin{center}
\tz[scale=1.2]{
  \draw[double strand=4pt, strA] (0,0) to[s] (1,1.5) to[-s] (2,3);
  \draw[double strand=4pt, strB] (2,0) to[s] (1,1.5) to[-s] (0,3);
  \mk{(0,0)}; \mk{(2,0)}; \mk{(0,3)}; \mk{(2,3)};
}
\end{center}

\SeeAlso{tikz test 08 knots, tikz test 12 double strands}

\end{document}
EOF

# Test 08: Knots
cat > "$NOTES_DIR/tikz test 08 knots.tex" << 'EOF'
\documentclass{gwiki}
\usepackage{gwiki-links}
\usepackage{tz}

\Title{tikz test 08 knots}
\Tags{tikz, visualization, test}

\begin{document}
\NoteHeader

Knot and crossing styles: \texttt{knot}, \texttt{over}, \texttt{crossing gap}. \allformats{tikz test 08 knots}

Navigation: \wref{tikz test 07 multiline} (previous) | \wref{tikz test 09 positioning} (next)

\section*{Basic Crossing}

\subsection*{Simple Over-Under}

\begin{center}
\tz{
  \draw[ultra thick, strA] (0,0) -- (2,2);
  \draw[ultra thick, strB, knot] (0,2) -- (2,0);
  \node at (1,-0.5) {Red over blue};
}
\end{center}

\subsection*{Using Over Style}

\begin{center}
\tz{
  \draw[ultra thick, colA] (0,0) -- (3,3);
  \draw[ultra thick, colB, over] (0,3) -- (3,0);
}
\end{center}

\section*{Multiple Crossings}

\subsection*{Trefoil Knot}

\begin{center}
\tz[scale=0.8]{
  % Simplified trefoil
  \draw[ultra thick, strM]
    (0,0) to[bend left=30] (2,1)
    to[bend left=30] (1,3)
    to[bend left=30] cycle;
  \draw[ultra thick, strM, knot]
    (0.5,0.5) to[bend right=20] (1.5,2);
}
\end{center}

\subsection*{Figure-Eight}

\begin{center}
\tz[scale=1.2]{
  \draw[ultra thick, blue] (0,0) .. controls (1,-0.5) and (2,0.5) .. (3,0);
  \draw[ultra thick, blue, knot] (0,1) .. controls (1,1.5) and (2,0.5) .. (3,1);
  \draw[ultra thick, blue] (3,0) .. controls (3.5,0.5) .. (3,1);
  \draw[ultra thick, blue, knot] (0,0) .. controls (-0.5,0.5) .. (0,1);
}
\end{center}

\subsection*{Crossing Gap Control}

\begin{center}
\tz{
  \draw[ultra thick, red, crossing gap=3pt] (0,0) -- (3,3);
  \draw[ultra thick, blue] (0,3) -- (3,0);
  \node[below] at (1.5,-0.3) {3pt gap};
}
\end{center}

\begin{center}
\tz{
  \draw[ultra thick, red, crossing gap=6pt] (0,0) -- (3,3);
  \draw[ultra thick, blue] (0,3) -- (3,0);
  \node[below] at (1.5,-0.3) {6pt gap};
}
\end{center}

\SeeAlso{tikz test 06 string diagrams, tikz test 11 layers}

\end{document}
EOF

echo "✓ Created tests 07-08"
# Continue with remaining tests...
