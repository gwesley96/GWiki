\NeedsTeXFormat{LaTeX2e}
\RequirePackage{silence}
\WarningFilter{latex}{You have requested document class}
\WarningFilter{latex}{You have requested package}
\ProvidesClass{gwiki}[2025/12/08 v1.0 GWiki LaTeX Class - Interconnected Note System]

\newcommand{\ctrsubordto}{section} % replace the name here of whichever level of header (e.g., section, subsection, subsubsection, etc.) you want the theorem (and thus the rest of the enunciations relying on it) to be siblings to. E.g,. use "section" if you want "Definition 1", then eg "Lemma 2", etc., instead of something like "Definition 0.1", then eg "Lemma 0.2".

%% ============================================================================
%% GWIKI DOCUMENT CLASS
%% A LaTeX class for interconnected mathematical/physics notes
%% Combines the best of cphysics.org, nLab, and Obsidian
%% ============================================================================

\RequirePackage{kvoptions,etoolbox}
\SetupKeyvalOptions{family=gwiki,prefix=gwiki@}

%% ----------------------------------------------------------------------------
%% TOGGLES
%% ----------------------------------------------------------------------------
\newcommand{\setToggle}[2][false]{\providetoggle{#2}\settoggle{#2}{#1}}
\forcsvlist{\setToggle}{%
  enableParskip,enableNoLimits,enableLeftRightReducePadding,%
  enableLeftRightIgnoreScripts,enableLabelNumberBeforeName,%
  enableBibliography,enableDisplayUncited,enableFancyhead,%
  enableIndex,enableBacklinks%
}

%% ----------------------------------------------------------------------------
%% OPTIONS
%% ----------------------------------------------------------------------------
\DeclareStringOption[article]{type}        % article, wiki, or note
\DeclareStringOption[]{gwikiid}            % Unique ID for this document
\DeclareStringOption[3pt plus 3pt minus 9pt]{displayMathPadding}
\DeclareStringOption[0.25in]{parindent}
\DeclareStringOption[12pt]{fontsize}
\DeclareStringOption[letterpaper]{paper}
\DeclareStringOption[1in]{margins}
\DeclareStringOption[]{maincounterparent}  % e.g., section, subsection, etc.

\DeclareBoolOption[false]{parskip}
\DeclareBoolOption[false]{nolimits}
\DeclareBoolOption[false]{reducepadding}
\DeclareBoolOption[false]{displayuncited}
\DeclareBoolOption[false]{ignorescripts}
\DeclareBoolOption[false]{labelnumberbeforename}
\DeclareBoolOption[false]{bibliography}
\DeclareBoolOption[false]{fancyhead}
\DeclareBoolOption[false]{index}
\DeclareBoolOption[false]{backlinks}
\DeclareBoolOption[false]{draft}

\ProcessKeyvalOptions*

%% ----------------------------------------------------------------------------
%% BASE CLASS
%% ----------------------------------------------------------------------------
\LoadClass[\gwiki@fontsize]{extarticle}

%% Apply toggles
\ifgwiki@ignorescripts\settoggle{enableLeftRightIgnoreScripts}{true}\fi
\ifgwiki@nolimits\settoggle{enableNoLimits}{true}\fi
\ifgwiki@reducepadding\settoggle{enableLeftRightReducePadding}{true}\fi
\ifgwiki@displayuncited\settoggle{enableDisplayUncited}{true}\fi
\ifgwiki@bibliography\settoggle{enableBibliography}{true}\fi
\ifgwiki@labelnumberbeforename\settoggle{enableLabelNumberBeforeName}{true}\fi
\ifgwiki@fancyhead\settoggle{enableFancyhead}{true}\fi
\ifgwiki@index\settoggle{enableIndex}{true}\fi
\ifgwiki@backlinks\settoggle{enableBacklinks}{true}\fi

%% ----------------------------------------------------------------------------
%% DISPLAY MATH SPACING
%% ----------------------------------------------------------------------------
\AtBeginDocument{
  \setlength{\abovedisplayskip}{\gwiki@displayMathPadding}
  \setlength{\belowdisplayskip}{\gwiki@displayMathPadding}
  \setlength{\abovedisplayshortskip}{\gwiki@displayMathPadding}
  \setlength{\belowdisplayshortskip}{\gwiki@displayMathPadding}
  \setlength{\parindent}{\gwiki@parindent}
}

%% Table of contents without page breaks
\let\oldtoc\tableofcontents
\renewcommand{\tableofcontents}{%
  \begingroup
  \let\cleardoublepage\relax
  \let\clearpage\relax
  \oldtoc
  \bigskip
  \endgroup
}

%% ============================================================================
%% SECTION FORMATTING (using titlesec)
%% ============================================================================
\RequirePackage[indentafter]{titlesec}

\titleformat{name=\section}{}{\sectionS\thetitle.}{0.8em}{\centering\scshape}
\titleformat{name=\subsection}[runin]{}{\sectionS\thetitle.}{0.5em}{\bfseries}[.]
\titleformat{name=\subsubsection}[runin]{}{\sectionS\thetitle.}{0.5em}{\underline}[.]
\titleformat{name=\paragraph,numberless}[runin]{}{}{\parindent}{\slshape}[.]
\titleformat{name=\subparagraph,numberless}[runin]{}{}{0em}{}[.]

\titlespacing*{\section}{0pt}{\bigskipamount}{2ex}
\titlespacing*{\subsection}{0pt}{\medskipamount}{2ex}
\titlespacing*{\subsubsection}{\smallskipamount}{2ex}{2ex}
\titlespacing*{\paragraph}{0em}{0em}{0.5em}
\titlespacing*{\subparagraph}{0em}{0em}{0.5em}

%% ============================================================================
%% CORE PACKAGES
%% ============================================================================
\RequirePackage[leqno]{amsmath}
\RequirePackage{amssymb,amsthm,stackrel}
\RequirePackage{standalone}
\RequirePackage{thmtools,thm-restate}
\RequirePackage{enumitem}
\RequirePackage{tikz}
\RequirePackage{tikz-cd}
\RequirePackage{quiver}
\RequirePackage{nicematrix}
\RequirePackage{filemod}
\RequirePackage{datetime2}
\RequirePackage{lastpage}
\RequirePackage{indentfirst}
\RequirePackage{chngcntr}
\RequirePackage{float}
\RequirePackage[footnotesize,bf]{caption}
\captionsetup{margin=0.75cm}
\RequirePackage[dvipsnames,svgnames]{xcolor}
\RequirePackage[protrusion=true,expansion=true,activate={true,nocompatibility}]{microtype}
\RequirePackage{newunicodechar}
\newunicodechar{∞}{\ensuremath{\infty}}
\newunicodechar{𝓒}{\ensuremath{\mathcal{C}}}

% More aggressive reductions
\microtypesetup{
  tracking=true,
  % spacing=true,
  stretch=10,     % allow more expansion
  shrink=20       % allow more shrinkage
}

% \SetTracking{encoding=*}{-20}


\iftoggle{enableParskip}{\RequirePackage{parskip}}{}

\iftoggle{enableIndex}{%
  \RequirePackage{imakeidx}
  \makeindex[columns=2, title=Alphabetical Index, intoc]
  \AtBeginDocument{\renewcommand{\defn}[1]{\emph{#1}\index{#1}}}
  \AtEndDocument{\printindex}
}{}

%% ============================================================================
%% HYPERREF AND CLEVEREF
%% ============================================================================
\RequirePackage[
  colorlinks=true,
  breaklinks=true,
  linkcolor=purple,
  filecolor=purple,
  urlcolor=blue,
  citecolor=blue,
  pdfpagemode=FullScreen,
  linktocpage=true,
  hyperfootnotes=true,
  pdfnewwindow=true,
  ocgcolorlinks
]{hyperref}

% Try zref-xr for better hyperlink support between documents
\RequirePackage{zref-xr}
\IfFileExists{gwiki-externaldocs.sty}{\RequirePackage{gwiki-externaldocs}}{}
\RequirePackage[capitalize,noabbrev]{cleveref}
\RequirePackage[\gwiki@paper,margin=\gwiki@margins]{geometry}

%% mathclap definition
\makeatletter
\providecommand*\mathclap[1]{\mathpalette\@mathclap{#1}}
\def\@mathclap#1#2{\hbox to 0pt{\hss$\m@th#1{#2}$\hss}}
\makeatother

%% ============================================================================
%% TOGGLE IMPLEMENTATIONS
%% ============================================================================
\iftoggle{enableNoLimits}{
  \newcommand{\redefOp}[1]{%
    \expandafter\let\csname old#1\expandafter\endcsname\csname#1\endcsname
    \expandafter\renewcommand\csname#1\endcsname{\csname old#1\endcsname\nolimits}
  }
  \forcsvlist{\redefOp}{sum,prod,bigcup,bigcap,bigvee,bigwedge,int,oint,bigotimes,bigoplus,coprod,bigsqcup,sup,liminf}
}{}

\iftoggle{enableLeftRightReducePadding}{%
  \let\originalleft\left
  \let\originalright\right
  \renewcommand{\left}{\mathopen{}\mathclose\bgroup\originalleft}
  \renewcommand{\right}{\aftergroup\egroup\originalright}
}{}

\iftoggle{enableFancyhead}{
  \RequirePackage{fancyhdr}
  \setlength{\headheight}{20pt}
  \lhead{}
  \RequirePackage{lastpage}
  \fancyfoot[C]{\small Page \thepage \hspace{1pt} of \pageref{LastPage}}
  \let\oldsubsection\subsection
  \renewcommand{\subsection}[1]{\oldsubsection{#1}\rhead{\hyperlink{toc}{\sectionS\small\arabic{section}.\arabic{subsection}: #1}}}
}{}

%% ============================================================================
%% ENUNCIATION ENVIRONMENTS (Theorems, Definitions, etc.)
%% ============================================================================
\makeatletter
\newcounter{mainctr}
\newcommand{\gwiki@mainctrparent}{} % Tracks which counter (if any) mainctr follows

\newcommand{\MainCounterWithin}[1]{%
  \edef\gwiki@tmpparent{#1}%
  % Detach from previous parent if there was one
  \ifdefempty{\gwiki@mainctrparent}{}{%
    \@ifundefined{c@\gwiki@mainctrparent}{}{%
      \counterwithout{mainctr}{\gwiki@mainctrparent}%
    }%
  }%
  % Attach to the requested parent (if provided and defined)
  \ifdefempty{\gwiki@tmpparent}{}{%
    \@ifundefined{c@\gwiki@tmpparent}{%
      \PackageWarning{gwiki}{Counter `\gwiki@tmpparent' undefined; leaving mainctr global}%
    }{%
      \counterwithin{mainctr}{\gwiki@tmpparent}%
    }%
  }%
  \renewcommand{\gwiki@mainctrparent}{\gwiki@tmpparent}%
  \setcounter{mainctr}{0}%
}

% Apply default parent from the class option (empty = global numbering)
\MainCounterWithin{\gwiki@maincounterparent}

\newcounter{alpha}
\renewcommand\thealpha{\Alph{alpha}}

%% Standard (unframed) enunciation
%% NOTE: #5 is the target counter name (e.g., 'theorem' or 'childofsection')
\newcommand{\defineStandardEnunciation}[5]{%
  \declaretheoremstyle[
    spaceabove=\parsep,
    spacebelow=\parsep,
    headpunct={},
    headfont=\upshape\bfseries,
    notebraces={(}{)},
    headformat={\NAME~\NUMBER\NOTE.},
    postheadhook={\phantom{}{}},
    #4
  ]{#1Style}%
  \declaretheorem[style=#1Style,name=#2,sibling=#5]{#1}%
  \declaretheorem[style=#1Style,name=#3,sibling=#5]{#1s}%
  \declaretheorem[style=#1Style,name=#2,sibling=alpha]{#1alpha}
  \declaretheorem[style=#1Style,name=#3,sibling=alpha]{#1salpha}
  \crefname{#1}{#2}{#3}%
  \crefname{#1alpha}{#2}{#3}%
  \crefname{#1salpha}{#2s}{#3}%
  \crefname{list#1}{#2}{#3}%
  \crefname{list#1s}{#3}{#3}%
}

%% Framed enunciation using tcolorbox
\RequirePackage[most,hooks]{tcolorbox}
\tcbset{
  framedStyle/.style={
    enhanced,
    breakable,
    enforce breakable,
    right=4pt,
    left=4pt,
    top=4pt,
    bottom=4pt,
    arc=0.75mm,
    boxrule=0.75mm,
    parbox=false,
    titlerule=0.2mm,
    colback=white,
    fonttitle=\bfseries,
    coltitle=black,
    colbacktitle=gray!20,
    toptitle=2pt,
    bottomtitle=2pt
  }
}

\iftoggle{enableLabelNumberBeforeName}{
  \swapnumbers
  \newcommand{\enunciationHeader}[3]{%
    #2~\ifstrempty{#3}{#1}{#1:#3}%
  }
}{
  \newcommand{\enunciationHeader}[3]{%
    #1\ifstrempty{#3}{#2}{#2:~#3}%
  }
}

\makeatletter
\newcommand{\defineFramedEnunciation}[5]{%
  \newtcolorbox{#1Frame}[2][]{framedStyle,title={##1},##2}%
  \newenvironment{framed#1}[1][]%
  {%
    \refstepcounter{#1}%
    \global\csdef{#1title@\csname the#1\endcsname}{##1}%
    \begin{#1Frame}%
    {#4,title={\enunciationHeader{#2}{\csname the#1\endcsname}{##1}}}%
  }%
  {\end{#1Frame}}%
}
\makeatother

%% MAIN DEFINITION COMMAND
\newcommand{\defineEnunciation}[6]{%
  \makeatletter
  % Check if #6 is a structural parent (empty, section, subsection) or a sibling
  \ifboolexpr{ test {\ifstrempty{#6}} or test {\ifstrequal{#6}{section}} or test {\ifstrequal{#6}{subsection}} }
  {%
    % Case 1: Root Driver (e.g. Theorem)
    \ifcsname c@childof#6\endcsname\else
      \newcounter{childof#6}%
      \ifstrempty{#6}{
         \counterwithout{childof}{section}% Global numbering (1, 2, 3...)
      }{
         \counterwithin{childof#6}{#6}% Sectional numbering (1.1, 1.2...)
      }%
    \fi
    \def\gwiki@targetCounter{childof#6}%
  }
  {%
    % Case 2: Sibling (e.g. Lemma sharing counter with Theorem)
    \def\gwiki@targetCounter{#6}%
  }%
  \makeatother
  \defineStandardEnunciation{#1}{#2}{#3}{#4}{\gwiki@targetCounter}%
  \defineFramedEnunciation{#1}{#2}{#4}{#5}{\gwiki@targetCounter}%
}

%% ----------------------------------------------------------------------------
%% ENUNCIATION CONFIGURATION
%% ----------------------------------------------------------------------------

%% DRIVER: Theorem determines the numbering style.
%% Use {} for global numbering (Definition 1, Lemma 2...)
%% Use {section} for per-section numbering (Definition 1.1, Lemma 1.2...)
\defineEnunciation{theorem}{Theorem}{Theorems}{bodyfont=\itshape}{colframe=blue, fontupper=\itshape}{\ctrsubordto}

%% SIBLINGS: All following environments share the 'theorem' counter
\defineEnunciation{corollary}{Corollary}{Corollaries}{bodyfont=\itshape}{colframe=gray, fontupper=\itshape}{theorem}
\defineEnunciation{lemma}{Lemma}{Lemmas}{bodyfont=\itshape}{colframe=Dandelion, fontupper=\itshape}{theorem}
\defineEnunciation{proposition}{Proposition}{Propositions}{bodyfont=\itshape}{colframe=purple, fontupper=\itshape}{theorem}
\defineEnunciation{claim}{Claim}{Claims}{bodyfont=\itshape}{colframe=teal, fontupper=\itshape}{theorem}
\defineEnunciation{step}{Step}{Steps}{bodyfont=\itshape}{colframe=orange, fontupper=\itshape}{theorem}
\defineEnunciation{construction}{Construction}{Constructions}{bodyfont=\upshape}{colframe=green, fontupper=\upshape}{theorem}
\defineEnunciation{question}{Question}{Questions}{bodyfont=\upshape}{colframe=red, fontupper=\upshape}{theorem}
\defineEnunciation{warning}{Warning}{Warnings}{bodyfont=\upshape}{colframe=magenta, fontupper=\upshape}{theorem}
\defineEnunciation{exercise}{Exercise}{Exercises}{bodyfont=\upshape}{colframe=violet, fontupper=\upshape}{theorem}
\defineEnunciation{example}{Example}{Examples}{bodyfont=\upshape}{colframe=ForestGreen, fontupper=\upshape}{theorem}
\defineEnunciation{definition}{Definition}{Definitions}{bodyfont=\upshape}{colframe=olive, fontupper=\upshape}{theorem}
\defineEnunciation{fact}{Fact}{Facts}{bodyfont=\upshape}{colframe=olive, fontupper=\upshape}{theorem}
\defineEnunciation{observation}{Observation}{Observations}{bodyfont=\upshape}{colframe=brown, fontupper=\upshape}{theorem}
\defineEnunciation{convention}{Convention}{Conventions}{bodyfont=\upshape}{colframe=pink, fontupper=\upshape}{theorem}
\defineEnunciation{remark}{Remark}{Remarks}{bodyfont=\upshape}{colframe=gray, fontupper=\upshape}{theorem}
\defineEnunciation{note}{Note}{Notes}{bodyfont=\upshape}{colframe=yellow, fontupper=\upshape}{theorem}
\defineEnunciation{notation}{Notation}{Notations}{bodyfont=\upshape}{colframe=blue!50, fontupper=\upshape}{theorem}
\defineEnunciation{axiom}{Axiom}{Axioms}{bodyfont=\upshape}{colframe=violet, fontupper=\upshape}{theorem}
\defineEnunciation{assumption}{Assumption}{Assumptions}{bodyfont=\upshape}{colframe=red, fontupper=\upshape}{theorem}
\defineEnunciation{algorithm}{Algorithm}{Algorithms}{bodyfont=\upshape}{colframe=red, fontupper=\upshape}{theorem}
\defineEnunciation{postulate}{Postulate}{Postulates}{bodyfont=\upshape}{colframe=red, fontupper=\upshape}{theorem}
%% Equation numbering linked to theorem counter
\makeatletter
\let\c@equation\c@theorem
\makeatother
\renewcommand{\theequation}{\textbf{\thetheorem}}

%% namedcref command
\makeatletter
\newcommand{\namedcref}[1]{%
  \begingroup
  \cref@gettype{#1}{\@tempa}%
  \ifx\@tempa\@empty{\cref{#1}}%
  \else\edef\@number{\getrefnumber{#1}}\ifcsdef{\@tempa title@\@number}{\csuse{\@tempa title@\@number}\space(\cref{#1})}{%
    \edef\@labelname{\getrefbykeydefault{#1}{name}{}}%
    \ifx\@labelname\@empty{\cref{#1}}\else{\nameref*{#1}\space(\cref{#1})}\fi%
  }\fi%
  \endgroup
}
\makeatother

%% ============================================================================
%% LISTS
%% ============================================================================
\RequirePackage{calc}
\SetEnumitemKey{widestlabel}{labelwidth = \widthof{\ref{enum-\EnumitemId}},after = \label{enum-\EnumitemId}}
\setlist[itemize]{font=\upshape,nosep,leftmargin=\parindent}
\newlist{lst}{enumerate}{4}
\setlist[lst]{%
  font=\upshape,
  label=(\roman*),
  nosep,
  itemsep=0.25ex,
  topsep=0.5ex,
  listparindent=\parindent,
  labelindent=0pt,
  widestlabel,
  leftmargin=!,
}

\makeatletter
\let\olditem\item
\renewcommand{\item}[1][]{%
  \ifx\relax#1\relax
    \olditem%
  \else
    \olditem[#1]\protected@edef\@currentlabel{#1}%
  \fi
}
\makeatother

%% ============================================================================
%% OTHER SETTINGS
%% ============================================================================
\makeatletter
\interfootnotelinepenalty=\@M
\makeatother
\sloppypar\sloppy
\allowdisplaybreaks

\let\pf\proof
\let\endpf\endproof
\newenvironment{soln}{\proof[Solution]}{\endproof}

\setlength{\footskip}{0.5in}

\makeatletter
\newcommand{\leqnomode}{\tagsleft@true}
\newcommand{\reqnomode}{\tagsleft@false}
\makeatother

%% ============================================================================
%% FONTS
%% ============================================================================
\RequirePackage{setspace}
\setstretch{1.05}
\RequirePackage[lining]{newpxtext}
\RequirePackage{newpxmath}
\RequirePackage{BOONDOX-uprscr}

%% ============================================================================
%% LOAD GWIKI PACKAGES
%% ============================================================================
\RequirePackage{gwiki-macros}
\RequirePackage{gwiki-links}
\RequirePackage{tz}

%% ============================================================================
%% DEFAULT FANCYHEAD FOR NOTES
%% ============================================================================
\RequirePackage{fancyhdr}
\makeatletter
\pagestyle{fancy}
\fancyhf{} % Clear all
\setlength{\headheight}{24pt}
% URL-encode the jobname by replacing spaces with %20 and removing quotes
\begingroup
\catcode`\%=12
\catcode`\ =12
\gdef\@spacechar{ }
\gdef\@percenttwenty{%20}
\endgroup

% Remove quotes from jobname (TeX adds them when spaces are present)
% Robust quote removal
\def\@zapquotes#1"#2"#3\@nil{#1#2}
\def\@removequotes#1{\expandafter\@zapquotes#1""\@nil}
\edef\@cleanjobname{\@removequotes\jobname}

\def\@urlencode#1{\expandafter\@urlencode@i#1 \@nil}
\def\@urlencode@i#1 #2\@nil{%
  #1%
  \ifx\@nil#2\@nil\else
    \@percenttwenty\@urlencode@i#2\@nil
  \fi
}

\edef\@encodedjobname{\expandafter\@urlencode\@cleanjobname\@empty}

\newcommand{\gwiki@firstheader}{%
  \fancyhead[R]{}%
}
\newcommand{\gwiki@firstfooter}{%
  \fancyfoot[C]{\scriptsize\color{gray!60}\thepage}%
  \fancyfoot[R]{\scriptsize\href{https://greysonwesley.com}{\textcolor{blue}{greysonwesley.com}}}%
}

\fancypagestyle{gwiki@first}{%
  \fancyhf{}%
  \gwiki@firstheader
  \gwiki@firstfooter
  \renewcommand{\headrulewidth}{0pt}%
}

\fancypagestyle{plain}{%
  \fancyhf{}%
  \gwiki@firstheader
  \gwiki@firstfooter
  \renewcommand{\headrulewidth}{0pt}%
}
\makeatother

\endinput
