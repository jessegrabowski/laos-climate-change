%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Text Area: 8in (include Runningheads) x 5in
%% ws-cce.cls   :   05-07-2024
%% Class file to use with ws-cce.tex written in Latex2E.
%% The content, structure, format and layout of this style file is the
%% property of World Scientific Publishing Co. Pte. Ltd.
%% Copyright 2024 by World Scientific Publishing Co.
%% All rights are reserved.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%

\NeedsTeXFormat{LaTeX2e}[1995/06/01]
\ProvidesClass{ws-cce}[2024/07/05 v1.5g Standardized LaTeX document class]
\@twosidetrue\@mparswitchtrue\@twocolumnfalse
\newif\if@openright
\@openrighttrue
\newif\if@restonecol
%
%
\newdimen\trimheight \trimheight9.71truein   %measure is 9.75truein
\newdimen\trimwidth \trimwidth6.48truein     %measure is 6.50truein
\newdimen\typeheight \typeheight48.1pc
\newdimen\typewidth \typewidth30pc
\newdimen\wsdraftrule \wsdraftrule=0pt
\newdimen\tempdimen
\newdimen\tablewidth
\newdimen\normaltextheight
\newbox\tempbox
\newdimen\tablewd
%

\DeclareOption{wsdraft}{\setlength\overfullrule{5pt}\wsdraftrule0.1pt}
\DeclareOption{final}{\setlength\overfullrule{0pt}}

\ExecuteOptions{a4paper,10pt,twoside,onecolumn,final}
\ProcessOptions
%
%\hoffset=-1.5cm
%\voffset=-0.5cm
%

\newcommand\appendixname{Appendix}
\newcommand\abstractname{Abstract}
\newcommand\bibname{References}%
\newcommand\contentsname{Contents}
\newcommand\indexname{Index}
\newcommand\figurename{Fig.}
\newcommand\tablename{Table}
\newcommand\partname{Part}
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Font Defs. %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\def\foliofont{\fontsize{8}{10}\selectfont}
\def\bibfont{\fontsize{9}{11}\selectfont}
\def\rhfont{\footnotesize\itshape{}}
\def\catchlinefont{\footnotesize}
\def\titlefont{\fontsize{10}{13}\bfseries\boldmath\selectfont\centering{}}
\def\authorfont{\footnotesize}
\def\affiliationfont{\centering\footnotesize\it}
\def\abstractfont{\footnotesize}
\def\datefont{\footnotesize}
\def\sectionfont{\bfseries\boldmath\rightskip2pc plus1fill{}}
\def\subsectionfont{\bfseries\boldmath\itshape\rightskip2pc plus1fill{}}
\def\subsubsectionfont{\itshape\rightskip2pc plus1fill{}}
\def\paragraphfont{\bfseries\boldmath}
\def\subparagraphfont{\itshape}
\def\figurecaptionfont{\footnotesize}
\def\tablefont{\footnotesize}
\def\tablecaptionfont{\footnotesize}
\def\tabnotefont{\footnotesize}
\def\TCHfont{\bf}
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Fonts %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\DeclareOldFontCommand{\rm}{\rmfamily}{\mathrm}
\DeclareOldFontCommand{\sf}{\sffamily}{\mathsf}
\DeclareOldFontCommand{\tt}{\ttfamily}{\mathtt}
\DeclareOldFontCommand{\bf}{\bfseries}{\mathbf}
\DeclareOldFontCommand{\it}{\itshape}{\mathit}
\DeclareOldFontCommand{\sl}{\slshape}{\@nomath\sl}
\DeclareOldFontCommand{\sc}{\scshape}{\@nomath\sc}
\DeclareRobustCommand\cal{\@fontswitch\relax\mathcal}
\DeclareRobustCommand\mit{\@fontswitch\relax\mathnormal}
\DeclareOldFontCommand{\bi}{\bfseries\itshape}{\@nomath\bi}
\renewcommand{\rmdefault}{cmr}%
%
\renewcommand\normalsize{%
   \@setfontsize\normalsize\@xpt{13}%\@xiiipt
   \abovedisplayskip 6\p@\@plus4\p@\@minus2\p@
   \abovedisplayshortskip\abovedisplayskip
   \belowdisplayshortskip\abovedisplayshortskip
   \belowdisplayskip\abovedisplayskip
   \let\@listi\@listI}
\normalsize
%
\newcommand\small{%
   \@setfontsize\small\@ixpt{11}%
   \abovedisplayskip 8\p@ \@plus3\p@ \@minus4\p@
   \abovedisplayshortskip \z@ \@plus2\p@
   \belowdisplayshortskip 4\p@ \@plus2\p@ \@minus2\p@
   \def\@listi{\leftmargin\leftmargini
               \topsep 4\p@ \@plus2\p@ \@minus2\p@
               \parsep 2\p@ \@plus\p@ \@minus\p@
               \itemsep \parsep}%
   \belowdisplayskip \abovedisplayskip}
%
\newcommand\footnotesize{%
   \@setfontsize\footnotesize\@viiipt{10}%
   \abovedisplayskip 6\p@ \@plus2\p@ \@minus4\p@
   \abovedisplayshortskip \z@ \@plus\p@
   \belowdisplayshortskip 3\p@ \@plus\p@ \@minus2\p@
   \def\@listi{\leftmargin\leftmargini
               \topsep 3\p@ \@plus\p@ \@minus\p@
               \parsep 2\p@ \@plus\p@ \@minus\p@
               \itemsep \parsep}%
   \belowdisplayskip \abovedisplayskip}
%
\newcommand\scriptsize{\@setfontsize\scriptsize\@viipt\@viiipt}
\newcommand\tiny{\@setfontsize\tiny\@vpt\@vipt}
\newcommand\large{\@setfontsize\large\@xiipt{14}}%
\newcommand\Large{\@setfontsize\Large\@xivpt{16}}%%
\newcommand\LARGE{\@setfontsize\LARGE\@xviipt{22}}
\newcommand\huge{\@setfontsize\huge\@xxpt{25}}
\newcommand\Huge{\@setfontsize\Huge\@xxvpt{30}}
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\setlength\parindent{1.5em}
%
\setlength\smallskipamount{3\p@ \@plus 1\p@ \@minus 1\p@}
\setlength\medskipamount{6\p@ \@plus 2\p@ \@minus 2\p@}
\setlength\bigskipamount{12\p@ \@plus 4\p@ \@minus 4\p@}
%
\setlength\headheight{5\p@}
\setlength\headsep   {19pt}
\setlength\topskip   {7\p@}
\setlength\footskip{22pt}
\setlength\maxdepth{4\p@}
%
%\setlength\@maxdepth\maxdepth
%
\setlength\textwidth{\typewidth}
\@settopoint\textwidth
\setlength\textheight\typeheight
\advance\textheight-\headheight
\advance\textheight-\headsep
\setlength\normaltextheight{\textheight}
%
\setlength\oddsidemargin{21mm}%.625in%
\setlength\evensidemargin{\trimwidth}
\addtolength\evensidemargin{-\textwidth}
\addtolength\evensidemargin{-\oddsidemargin}
\setlength\topmargin{.85926in}%
%
\setlength\marginparwidth{.75in}
\setlength\marginparsep{7\p@}
\setlength\marginparpush{5\p@}
%
\setlength\footnotesep{6\p@}
\setlength{\skip\footins}{18\p@ \@plus 5\p@ \@minus 2\p@}
%
\setlength\floatsep    {18\p@ \@plus 2\p@ \@minus 2\p@}
\setlength\textfloatsep{18\p@ \@plus 2\p@ \@minus 4\p@}
\setlength\intextsep   {18\p@ \@plus 2\p@ \@minus 2\p@}
\setlength\dblfloatsep    {18\p@ \@plus 2\p@ \@minus 2\p@}
\setlength\dbltextfloatsep{18\p@ \@plus 2\p@ \@minus 4\p@}
\setlength\@fptop{0\p@}
\setlength\@fpsep{8\p@ \@plus 2fil}
\setlength\@fpbot{0\p@ \@plus 1fil}
\setlength\@dblfptop{0\p@ \@plus 1fil}
\setlength\@dblfpsep{8\p@ \@plus 2fil}
\setlength\@dblfpbot{0\p@ \@plus 1fil}
%
\setlength\partopsep{0\p@}
\setlength\lineskip{1\p@}
\setlength\normallineskip{1\p@}%
\renewcommand\baselinestretch{}%{}
\setlength\parskip{0\p@}
%
\@lowpenalty   51
\@medpenalty  151
\@highpenalty 301
%
\setcounter{topnumber}{3}
\renewcommand\topfraction{.98}
\setcounter{bottomnumber}{3}
\renewcommand\bottomfraction{.98}
\setcounter{totalnumber}{6}
\renewcommand\textfraction{.01}
\renewcommand\floatpagefraction{.98100}
\setcounter{dbltopnumber}{2}
\renewcommand\dbltopfraction{.981}
\renewcommand\dblfloatpagefraction{.99}
%
\setlength\arraycolsep{1.5\p@}
\setlength\tabcolsep{6\p@}
\setlength\arrayrulewidth{.4\p@}
\setlength\doublerulesep{2\p@}
\setlength\tabbingsep{\labelsep}
%\skip\@mpfootins = \skip\footins
%
\setlength\fboxsep{3\p@}
\setlength\fboxrule{.4\p@}
%
\setlength\columnsep{10\p@}
\setlength\columnseprule{0\p@}
%
%
\DeclareMathSizes{28}{28}{25}{20}
\DeclareMathSizes{24}{24}{21}{18}
\DeclareMathSizes{22}{22}{19}{17}
\DeclareMathSizes{20}{20}{17}{15}
\DeclareMathSizes{18}{18}{15}{10}
\DeclareMathSizes{12}{11}{8}{5}
\DeclareMathSizes{11}{11}{8}{5}
\DeclareMathSizes{10}{10}{7}{5}
\DeclareMathSizes{9.5}{9}{7}{5}
\DeclareMathSizes{9}{9}{7}{5}
\DeclareMathSizes{8}{8}{6}{5}
\DeclareMathSizes{7}{7}{5}{5}
\DeclareMathSizes{6}{6}{5}{5}
\DeclareMathSizes{5}{5}{5}{5}

\def\cdash{$^{\raisebox{-0.5pt}{\hbox{--}}}$}

\def\bm#1{\mathchoice
	{\mbox{\boldmath$#1$}}%
          {\mbox{\boldmath$#1$}}%
          {\mbox{\boldmath$\scriptstyle#1$}}%
          {\mbox{\boldmath$\scriptscriptstyle#1$}}}%
%
%%%%%%%%%%%%%%%%%%%%%%%%%%% Article FM %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\def\title#1{\gdef\@title{{{#1}}}}
\def\subtitle#1{\titlefont :~#1}
\newcommand\maketitle{\par
  \begingroup
   \renewcommand\thefootnote{\@fnsymbol\c@footnote}%
    \def\@makefnmark{\rlap{\@textsuperscript{\normalfont\@thefnmark}}}%
    \long\def\@makefntext##1{\noindent
	\@textsuperscript{\normalfont\@thefnmark}{##1}}%
      \newpage
      \global\@topnum\z@
      \@maketitle
    \thispagestyle{plain}\@thanks
  \endgroup
  \setcounter{footnote}{0}%
  \global\let\thanks\relax
  \global\let\maketitle\relax
  \global\let\@maketitle\relax
  \global\let\@thanks\@empty
  \global\let\@author\@empty
  \global\let\@title\@empty
  \global\let\title\relax
  \global\let\author\relax
}
\def\@maketitle{%
  \newpage
  \null
  \vspace*{-10pt}
   \vspace*{-25pt}% to have the bylines on the beginning of the page
  \@clinebuf
  \vspace*{52pt}
  \begin{center}%
  \let\footnote \thanks
  {\titlefont\@title \par}%
  \vspace*{28pt}
  \@aabuffer\par
  \end{center}%
}
%
\def\thebepage{\thepage}
\def\theeepage{\pageref{eof}}
%
\newenvironment{history}{%
	\addvspace{-2pt plus-2pt minus-2pt}
   \authorfont\begin{center}\vskip-\lastskip
}{%
   \end{center}
	\addvspace{15pt plus2pt minus2pt}
}

\def\email#1{\it #1\par}
\def\http#1{{\it http://#1}\par}
\def\url#1{{\it #1}\par}
\def\received#1{Received~#1\par}
\def\revised#1{Revised~#1\par}
\def\accepted#1{Accepted~#1\par}
\def\published#1{Published~#1\par}
\def\comby#1{\par\addvspace{1\baselineskip}Communicated\ by~#1\par}
%
\def\@clinebuf{}
\def\catchline#1#2#3#4#5{\expandafter\def\expandafter\@clinebuf\expandafter
	{\@clinebuf\catchlinefont
	\noindent Climate Change Economics\par
%	\noindent Vol.\ {#1}, \No\ {#2} (#3)\ \thebepage--\theeepage\par
	\noindent \copyright\ World Scientific Publishing Company\par
	\noindent\vskip-\baselineskip \hphantom{#4 \hskip2em #5}
	}\relax\par
	}
%
\def\No{No.}
%
\def\@aabuffer{}
\def\author#1{\expandafter\def\expandafter\@aabuffer\expandafter
	{\@aabuffer{\authorfont{{{#1}}}}\relax\par
	\vspace*{3pt}}}
%
\def\address#1{\expandafter\def\expandafter\@aabuffer\expandafter
	{\@aabuffer{\affiliationfont{#1}}\relax\par
	\vspace*{13pt}}}
%
\def\keywords#1{\par
	\vspace*{8pt}
	{\authorfont{\leftskip18pt\rightskip\leftskip
	\noindent{\it Keywords}\/:\ #1\par}}\par}
%
\def\ccode#1{\par
	\vspace*{8pt}
	{\authorfont{\leftskip18pt\rightskip\leftskip
	\noindent #1\par}}\par}

%
\def\category#1#2{\par
	\vspace*{8pt}
	{\authorfont{\leftskip18pt\rightskip\leftskip
	\noindent{\it Categories}\/:\ #1:\ #2\par}}\par}
%
\newenvironment{abstract}{\par%
	\abstractfont
  	\noindent\leftskip18pt\rightskip18pt
}{%
  \par}
%
\newenvironment{otherinfo}{%
	\addvspace{-2pt plus-2pt minus-2pt}
   \authorfont\begin{center}%\vskip-\lastskip
}{%
   \end{center}
	\addvspace{15pt plus2pt minus2pt}
}
%
\newenvironment{dedication}{%
	\addvspace{-2pt plus-2pt minus-2pt}
   \authorfont\begin{center}%\vskip-\lastskip
}{%
   \end{center}
	\addvspace{15pt plus2pt minus2pt}
}
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%% Sectioning %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\setcounter{secnumdepth}{3}
\newcounter {section}
\newcounter {subsection}[section]
\newcounter {subsubsection}[subsection]
\newcounter {paragraph}[subsubsection]
\newcounter {subparagraph}[paragraph]
\renewcommand\thesection      {\arabic{section}}
\renewcommand\thesubsection   {\thesection.\arabic{subsection}}
\renewcommand\thesubsubsection{\thesubsection .\arabic{subsubsection}}
\renewcommand\theparagraph    {\thesubsubsection.\arabic{paragraph}}
\renewcommand\thesubparagraph {\theparagraph.\arabic{subparagraph}}
%
\newcommand\section{\@startsection{section}{1}{\z@}{-18pt \@plus-3pt minus-6pt}{5pt}{\sectionfont}}
\newcommand\subsection{\@startsection{subsection}{2}{\z@}{-18pt \@plus-3pt minus-6pt}{5pt}{\subsectionfont}}
\newcommand\subsubsection{\@startsection{subsubsection}{3}{\z@}{-18pt \@plus-3pt minus-3pt}{5pt}{\subsubsectionfont}}
\newcommand\paragraph{\@startsection{paragraph}{4}{\z@}{12pt \@plus -3pt}{-.5em}{\paragraphfont}}
\newcommand\subparagraph{\@startsection{subparagraph}{5}{\parindent}{3.25ex \@plus1ex}{-1em}{\subparagraphfont}}
%
\def\@seccntformat#1{{\upshape{\csname the#1\endcsname.}}\hskip .5em}
%
%\gdef\@author{}
%
%%%%%%%%%%%%%%%%%%%%%%%% Table of Contents %%%%%%%%%%%%%%%%%%%%%%%
%
\newcommand\@pnumwidth{1.55em}
\newcommand\@tocrmarg{2.55em}
\newcommand\@dotsep{4.5}
\setcounter{tocdepth}{3}
\newcommand\tableofcontents{%
    \section*{\contentsname
        \@mkboth{%
           \contentsname}{\contentsname}}%
    \@starttoc{toc}%
    }
\newcommand\l@section[2]{%
  \ifnum \c@tocdepth >\z@
    \addpenalty\@secpenalty
    \addvspace{1.0em \@plus\p@}%
    \setlength\@tempdima{1.5em}%
    \begingroup
      \parindent \z@ \rightskip \@pnumwidth
      \parfillskip -\@pnumwidth
      \leavevmode \bfseries
      \advance\leftskip\@tempdima
      \hskip -\leftskip
      #1\nobreak\hfil \nobreak\hbox to \@pnumwidth{\hss #2}\par
    \endgroup
  \fi}
\newcommand\l@subsection{\@dottedtocline{2}{1.5em}{2.3em}}
\newcommand\l@subsubsection{\@dottedtocline{3}{3.8em}{3.2em}}
\newcommand\l@paragraph{\@dottedtocline{4}{7.0em}{4.1em}}
\newcommand\l@subparagraph{\@dottedtocline{5}{10em}{5em}}
\newcommand\listoffigures{%
    \section*{\listfigurename
      \@mkboth{\listfigurename}%
              {\listfigurename}}%
    \@starttoc{lof}%
    }
\newcommand\l@figure{\@dottedtocline{1}{1.5em}{2.3em}}
\newcommand\listoftables{%
    \section*{\listtablename
      \@mkboth{%
          \listtablename}{\listtablename}}%
    \@starttoc{lot}%
    }
\let\l@table\l@figure
%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%Lists %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\def\@listI{\leftmargin\leftmargini
            \listparindent\itemindent
            \parsep \z@\labelsep.5em
            \topsep 6.5\p@ \@plus3\p@% \@minus2\p@
            \itemsep0\p@}
%
\let\@listi\@listI
\@listi
%
\def\@listii {\leftmargin\leftmarginii
              \labelwidth\leftmarginii
              \advance\labelwidth-\labelsep
              \topsep    3.5\p@ \@plus2\p@ \@minus\p@
              \parsep    \z@
              \itemsep\z@}
\def\@listiii{\leftmargin\leftmarginiii
              \labelwidth\leftmarginiii
              \advance\labelwidth-\labelsep
              \topsep 3.5\p@ \@plus\p@\@minus\p@
              \parsep \z@
             % \partopsep \p@ \@plus\z@ \@minus\p@
              \itemsep0\p@}%
\def\@listiv {\leftmargin\leftmarginiv
              \labelwidth\leftmarginiv
              \advance\labelwidth-\labelsep}
\def\@listv  {\leftmargin\leftmarginv
              \labelwidth\leftmarginv
              \advance\labelwidth-\labelsep}
\def\@listvi {\leftmargin\leftmarginvi
              \labelwidth\leftmarginvi
              \advance\labelwidth-\labelsep}
%
\setlength\leftmargini{3pc}
\setlength\leftmarginii{2.2em}
\setlength\leftmarginiii{1.87em}
\setlength\leftmarginiv{1.7em}
\setlength\leftmarginv{1em}
\setlength\leftmarginvi{1em}
\setlength\leftmargin{\leftmargini}
\setlength\listparindent{\parindent}
\setlength\labelsep{.5em}
\setlength\labelwidth{\leftmargini}
\addtolength\labelwidth{-\labelsep}
\renewcommand\theenumi{\arabic{enumi}}
\renewcommand\theenumii{\alph{enumii}}
\renewcommand\theenumiii{\roman{enumiii}}
\renewcommand\theenumiv{\Alph{enumiv}}
\newcommand\labelenumi{(\theenumi)}
\newcommand\labelenumii{(\theenumii)}
\newcommand\labelenumiii{\theenumiii.}
\newcommand\labelenumiv{\theenumiv.}
\renewcommand\p@enumii{\theenumi}
\renewcommand\p@enumiii{\theenumi(\theenumii)}
\renewcommand\p@enumiv{\p@enumiii\theenumiii}
\newcommand\labelitemi{$\m@th\bullet$}
\newcommand\labelitemii{\normalfont\bfseries --}
\newcommand\labelitemiii{$\m@th\ast$}
\newcommand\labelitemiv{$\m@th\cdot$}
%
\def\enummax#1{\setbox\tempbox=\hbox{#1\hskip\labelsep}%
  \expandafter\global\csname leftmargin\romannumeral\the\@enumdepth\endcsname\wd\tempbox}
%
\def\enumerate{\@ifnextchar[{\@enumerate}{\@enumerate[\csname label\@enumctr\endcsname]}}
%
\def\@enumerate[#1]{\ifnum \@enumdepth >3 \@toodeep\else
      \advance\@enumdepth \@ne\edef\@enumctr{enum\romannumeral\the\@enumdepth}%
      \enummax{#1}\list
      {\csname label\@enumctr\endcsname}{\usecounter
        {\@enumctr}\def\makelabel##1{\hss\llap{##1}}}\fi}
%
\let\Item\item
\newenvironment{enumeroman}{%
  \def\theenumi{\roman{enumi}}\def\theenumii{\roman{enumii}}%
  \def\labelenumi{(\theenumi)}\def\labelenumii{(\theenumii)}%
		\let\item\Item
  \begin{enumerate}%
}{%
  \end{enumerate}}
%
\newenvironment{alphlist}{%
  \def\theenumi{\alph{enumi}}\def\theenumii{\alph{enumii}}%
  \def\labelenumi{(\theenumi)}\def\labelenumii{(\theenumii)}%
		\let\item\Item
  \begin{enumerate}%
}{%
  \end{enumerate}}
%
\newenvironment{arabiclist}{%
	\def\theenumi{\arabic{enumi}}\def\theenumii{\arabic{enumii}}
	\def\labelenumi{(\theenumi)}\def\labelenumii{(\theenumii)}%
	\let\item\Item
	\begin{enumerate}
	}{%
	\end{enumerate}}
%
\newenvironment{romanlist}{%
	\def\theenumi{\roman{enumi}}\def\theenumii{\roman{enumii}}
	\def\labelenumi{(\theenumi)}\def\labelenumii{(\theenumii)}%
	\let\item\Item
	\begin{enumerate}
	}{%
	\end{enumerate}}
%
\newenvironment{itemlist}{%
	\def\labelenumi{\labelitemi}
	\let\item\Item
	\begin{enumerate}
	}{%
	\end{enumerate}}
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%Lists %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\newenvironment{description}
               {\list{}{\labelwidth\z@ \itemindent-\leftmargin
                        \let\makelabel\descriptionlabel}}
               {\endlist}
\newcommand*\descriptionlabel[1]{\hspace\labelsep
                                \normalfont\bfseries #1}
%
\newenvironment{unnumlist}{%
	\let\item\Item
  	\leftmargini2pc
   	\ifnum \@enumdepth >3 \@toodeep\else
      	\advance\@enumdepth \@ne
      	\list{}{\itemindent-2pc\topsep6pt
              \def\makelabel##1{\hss\llap{##1}}}%
   \fi
}{%
  \endlist}
%
%%%%%%%%%%%%%%%%%%%%%%%%%% Poetry %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\newenvironment{verse}
               {\let\\\@centercr
                \list{}{\itemsep      \z@
                        \itemindent   -1.5em%
                        \listparindent\itemindent
                        \rightmargin  \leftmargin
                        \advance\leftmargin 1.5em}%
                \item\relax}
               {\endlist}
\let\poetry\verse
\let\endpoetry\endverse
%
%%%%%%%%%%%%%%%%%%%%%%%% Extract %%%%%%%%%%%%%%%%%%%%%%%
%
\newenvironment{quotation}
               {\list{}{\listparindent 1.5em%
                        \itemindent    \listparindent
                        \rightmargin   \leftmargin
                        \parsep        \z@ \@plus\p@}%
                \item\relax}
               {\endlist}
\newenvironment{quote}
               {\list{}{\rightmargin\leftmargin}%
                \item\relax}
               {\endlist}
%
\let\extract\quotation
\let\endextract\endquotation
%
\def\source#1{\par\hspace*{\fill}{\it#1}\par}
%
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Maths %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\renewcommand\theequation{\arabic{equation}}
%
\def\bstrut{\vrule width0pt depth5pt}
\def\tstrut{\vrule width0pt height10pt}
\jot=3pt
%

%\renewenvironment{equation}{\@equation}{\end@equation}
%
\def\refstepeqcnt{\refstepcounter{equation}}
\def\eqnnum{\displaywidth\linewidth\hbox{\@eqnnum}}
%
\def\@equation{\let\topsep\abovedisplayskip\@beginparpenalty\predisplaypenalty\@endparpenalty\postdisplaypenalty
     \refstepeqcnt
     \trivlist \item[]\leavevmode
       \hbox to\linewidth\bgroup\hfill $\m@th% $
       \displaystyle}%
\def\end@equation{$\hfill\eqnnum\egroup\endtrivlist}
%
\renewenvironment{eqnarray}{%
   \stepcounter{equation}%
   \def\@currentlabel{\p@equation\theequation}%
   \global\@eqnswtrue
   \m@th
   \global\@eqcnt\z@
   \tabskip\@centering
   \let\\\@eqncr
   $$\everycr{}\halign to\displaywidth\bgroup
       \hskip\@centering$\displaystyle\tabskip\z@skip{##}$\@eqnsel
      &\global\@eqcnt\@ne\hskip \tw@\arraycolsep \hfil${##}$\hfil
      &\global\@eqcnt\tw@ \hskip \tw@\arraycolsep
         $\displaystyle{##}$\hfil\tabskip\@centering
      &\global\@eqcnt\thr@@ \hb@xt@\z@\bgroup\hss##\egroup
         \tabskip\z@skip
      \cr}
        {%
      \@@eqncr
      \egroup
      \global\advance\c@equation\m@ne
   $$\global\@ignoretrue
}
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Floats %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\def\FigName{figure}%
\def\alttext#1{\relax}%
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\def\figurename{Figure}
\newcounter{figure}
\renewcommand\thefigure{\@arabic\c@figure}
\def\fps@figure{tbp}
\def\ftype@figure{1}
\def\ext@figure{lof}
\def\fnum@figure{\figurename~\thefigure}
\newenvironment{figure}
               {\@float{figure}}
               {\end@float}
\newenvironment{figure*}
               {\@dblfloat{figure}}
               {\end@dblfloat}
%
%%%%%%%%%%%%%%%%%%%%%%%%%% Tables %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\newcounter{table}
\def\tablename{Table}
\renewcommand\thetable{\@arabic\c@table}
\def\fps@table{tbp}
\def\ftype@table{2}
\def\ext@table{lot}
\def\fnum@table{\tablename~\thetable}
\newenvironment{table}
               {\@float{table}}
               {\end@float}
\newenvironment{table*}
               {\@dblfloat{table}}
               {\end@dblfloat}
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\def\tableformat#1{\centerline{#1}}
\newdimen\tabledim
\long\def\tbl#1#2{%
\global\setbox\tempbox\hbox{\tablefont #2}%
 \global\tabledim\wd\tempbox
 \tableformat{\vbox{\hsize\tabledim
                   \caption{#1}
                   \box\tempbox}}%
}
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%\long\def\ttbl#1#2#3{%
%	\parindent\z@
%	\noindent
%  	\tablecaptionfont
%	\caption{#2}%
%	\tablewd\hsize
%	\advance\tablewd-#1
%  	\global\divide\tablewd\tw@
%	\ifdim \wd\wscaptionbox<#1
%	\centerline{\unhbox\wscaptionbox}
%	\else
%  	{\leftskip\tablewd% plus1fill{}
%	\rightskip\tablewd% plus1fill{}
%  	\unhbox\wscaptionbox\par}
%	\fi
% 	\vskip-8pt
%	\centerline{#3}
%}%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\newenvironment{InTextTable}{%
 	\par\addvspace{16pt plus6pt minus6pt}%
 	\begin{center}
	\tablecaptionfont\noindent\ignorespaces
}{%
   	\end{center}
	\par\addvspace{17pt plus6pt minus6pt}}
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\def\tabnotehead{Note}
\def\tabsourcehead{Source}
\newenvironment{tabnote}{%
   \par\addvspace{2pt}
   \setbox\tempbox\vbox\bgroup\hsize\tabledim\parindent12pt
   \tabnotefont
   \@ifnextchar[{\@tabnote}{\@tabnote[\tabnotehead]}%
}{%
		\par\egroup
   \tableformat{\box\tempbox}}
%
\def\@tabnote[#1]{\vskip6pt\noindent\def\@Tempa{#1}\ifx\@Tempa\@empty\hskip0pt\else{\it#1}:\hskip5pt\ignorespaces\fi}
%
%%
\newenvironment{tabfootnote}{%
   \par\addvspace{2pt}
   \setbox\tempbox\vbox\bgroup\hsize\tabledim\parindent12pt
   \tabnotefont
}{%
		\par\egroup
   \tableformat{\box\tempbox}}
%
%%
\def\tabmark#1{\noindent\hbox{\normalsize$\m@th^{#1}$}\ignorespaces}
%
\newenvironment{tabsource}{%
   \let\tabnotehead\tabsourcehead
   \begin{tabnote}
}{%
   \end{tabnote}
}
%
\def\Hline{%
  \noalign{\ifnum0=`}\fi\hrule \@height 2\arrayrulewidth \futurelet
   \@tempa\@xhline}
%
\def\x{@{\extracolsep{\fill}}}
\def\toprule{\Hline\\[-7.5pt]}
\def\colrule{\\[-7.5pt]\hline\\[-7.5pt]}
\def\TMcolrule{\\[-9.5pt]\hline\\[-9.5pt]}
\def\botrule{\\[-9pt]\Hline}
\def\crule#1{\\[-10pt]#1\\[-6pt]}
%
%%%%%%%%%%%%%%%%%%%%%%%% Caption %%%%%%%%%%%%%%%%%%%%%%%
%
\newlength\abovecaptionskip
\newlength\belowcaptionskip
\setlength\abovecaptionskip{10\p@}
%\setlength\belowcaptionskip{0\p@}
\setlength\belowcaptionskip{4\p@}
\long\def\@makecaption#1#2{%
  \figurecaptionfont
  \vskip\abovecaptionskip
  \sbox\@tempboxa{#1. #2}%
  \ifdim \wd\@tempboxa >\hsize
    #1. #2\par
  \else
    \global \@minipagefalse
    \hbox to \hsize{\hfil\box\@tempboxa\hfil}%
  \fi
  \vskip\belowcaptionskip}
%
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Footnote %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\renewcommand\footnoterule{%
  \kern-3\p@
  \hrule depth0pt height0pt \@width.2\columnwidth
  \kern2.6\p@}
\newcommand\@makefntext[1]{%
    \parindent 1em%
    \noindent
     \@makefnmark#1}
%
\def\@fnsymbol#1{\ensuremath{\ifcase#1\or *\or \dagger\or \ddagger\or
   	\mathchar "278\or \mathchar "27B\or \|\or **\or \dagger\dagger
   	\or \ddagger\ddagger \else\@ctrerr\fi}}
%
%\def\thefootnote{\alph{footnote}}
%\def\@makefnmark{{$^{\rm \@thefnmark}$}}
\def\thefootnote{\arabic{footnote}}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Page Style %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\mark{{}{}}
%
\def\ps@plain{%
     \let\@mkboth\@gobbletwo
     \let\@oddhead\@empty
%    \def\@oddfoot{\hfill\mbox{\lower12pt\hbox{\foliofont\thepage}}\hfill}%
     \def\@oddfoot{\hfill\mbox{\hbox{\foliofont\thepage}}\hfill}%
     \let\@evenhead\@empty
     \let\@evenfoot\@oddfoot}
%
\def\RightMark{}
%
\def\ps@headings{%
    \let\@oddfoot\@empty
    \let\@evenfoot\@empty
    \def\@evenhead{\rhfont{\upshape{\thepage}}\hskip1em\leftmark\hfill}%
    \def\@oddhead{\hfill\rhfont\rightmark\hskip1em{\upshape{\thepage}}}%
    \let\@mkboth\markboth
    \def\authormark##1{\markboth{##1}{\RightMark}}%
    \def\chaptermark##1{\gdef\RightMark{##1}\markright{##1}}}%
    %\def\sectionmark##1{\gdef\RightMark{##1}\markright{##1}}}%
%
\def\ps@myheadings{%
    \let\@oddfoot\@empty\let\@evenfoot\@empty
    \def\@evenhead{\rlap{\foliofont \thepage}\hfill{\rhfont\leftmark}\hfill}%
    \def\@oddhead{\hfill{\rhfont\rightmark}\hfill{\foliofont\thepage}}%
    \let\@mkboth\@gobbletwo
    \let\chaptermark\@gobble
    \let\sectionmark\@gobble}
%
\def\ps@pblind{%
	\let\@mkboth\@gobbletwo
	\def\@evenhead{}%
	\def\@oddhead{}
	\def\@oddfoot{\hfill\mbox{\lower8pc\hbox{}}\hfill}
   \let\@evenfoot\@oddfoot}
%
%%%%%%%%%%%%%%%%%%%%%%%%%%% Theorem Environments %%%%%%%%%%%%%%%%%%%%%%%%%%
%
\def\@xthm#1#2{\@begintheorem{#2}{\csname the#1\endcsname}{}\ignorespaces}

\def\@ythm#1#2[#3]{\@opargbegintheorem{#2}{\csname
       the#1\endcsname}{#3}\ignorespaces}%
%
\def\@begintheorem#1#2#3{\par\addvspace{8pt plus3pt minus2pt}%
              \noindent{\csname#1headfont\endcsname#1\ \ignorespaces#3 #2.}%
              \csname#1font\endcsname\hskip.5em\ignorespaces}
\def\@endtheorem{\par\addvspace{8pt plus3pt minus2pt}\@endparenv}
%
\def\@opargbegintheorem#1#2#3{\par\addvspace{6pt plus3pt minus2pt}%
	\def\@tempa{#3}%
	\noindent{\bf #1 #2 \ifx\@tempa\empty\unskip\else\unskip\ (#3).\fi\hskip.5em}\csname#1font\endcsname\ignorespaces
%	\noindent{\bf #2 \ifx\@tempa\empty\unskip\else\unskip: #3\fi\hskip1em}\it
\ignorespaces}
%
\def\@endtheorem{\par\addvspace{6pt plus3pt minus2pt}}
%
\newif\iflogo
\def\prbox{\hbox to \hsize{\hfill\fboxsep0pt\fbox{\phantom{\vrule width5pt height5pt depth0pt}}}\global\logofalse}
%
%
\newenvironment{proof}{%
	\par\addvspace{12pt plus3pt minus3pt}
   \global\logotrue
   \@ifnextchar[{\@proof}{\@proof[Proof]}%
   }{%
	\par\iflogo\vskip-\lastskip
	\vskip-\baselineskip\prbox\par
	\addvspace{12pt plus3pt minus3pt}\fi}
%
\def\@proof[#1]{\noindent{\normalfont\bfseries#1.}\hskip.5em\ignorespaces}
%
\newtheorem{theorem}{Theorem}%[section]
\newcommand\theorembodyfont{\itshape}
\newtheorem{lemma}{Lemma}%[section]
\newcommand\lemmabodyfont{\itshape}
\newtheorem{proposition}{Proposition}%[section]
\newcommand\propositionbodyfont{\itshape}
\newtheorem{corollary}{Corollary}%[section]
\newcommand\corollarybodyfont{\itshape}
\newtheorem{assertion}{Assertion}%[section]
\newcommand\assertionbodyfont{\itshape}
%
\newtheorem{algorithm}{Algorithm}%[section]
\newcommand\algorithmbodyfont{\upshape}
\newtheorem{answer}{Answer}%[section]
\newcommand\answerbodyfont{\upshape}
\newtheorem{assumption}{Assumption}%[section]
\newcommand\assumptionbodyfont{\upshape}
\newtheorem{comment}{Comment}%[section]
\newcommand\commentbodyfont{\upshape}
\newtheorem{definition}{Definition}%[section]
\newcommand\definitionbodyfont{\upshape}
\newtheorem{example}{Example}%[section]
\newcommand\examplebodyfont{\upshape}
\newtheorem{remark}{Remark}%[section]
\newcommand\remarkbodyfont{\upshape}
\newtheorem{solution}{Solution}%[section]
\newcommand\solutionbodyfont{\upshape}
%
\let\Theoremheadfont\bfseries
\let\Corollaryheadfont\bfseries
\let\Propositionheadfont\bfseries
\let\Lemmaheadfont\bfseries
\let\Definitionheadfont\bfseries
\let\Remarkfont\upshape
\def\Exampleheadfont{\bfseries}
\def\Assumptionheadfont{\bfseries}
\def\Remarkheadfont{\bfseries}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Bibliography %%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%%%%%%%%%%%%%%%% CITATIONS FOR NAMES OF AUTHORS AND YEAR %%%%%%%%%%%%%%%
%
\let\@internalcite\cite
\def\cite{\def\@citeseppen{-1000}%
    %\def\@cite##1##2{[{##1\if@tempswa , ##2\fi}]}%  %[Simon (1995)]
     \def\@cite##1##2{{##1\if@tempswa , ##2\fi}}%    %Simon (1995)
     \def\citeauthoryear##1##2{##1, ##2}\@internalcite}
%
\def\shortcite{\def\@citeseppen{1000}%
    \def\@cite##1##2{[{##1\if@tempswa , ##2\fi}]}%
    \def\citeauthoryear##1##2{##2}\@internalcite}
%
\def\citeauthor#1{\def\@citeseppen{1000}%
    \def\@cite##1##2{{##1\if@tempswa , ##2\fi}}%
    \def\citeauthoryear##1##2{##1}\@citedata{#1}}
%
\def\citeyear#1{\def\@citeseppen{1000}%
    \def\@cite##1##2{{##1\if@tempswa , ##2\fi}}%
    \def\citeauthoryear##1##2{##2}\@citedata{#1}}
%
\def\@citedata#1{\@tempswafalse%
    \if@filesw\immediate\write\@auxout{\string\citation{#1}}\fi
  \def\@citea{}\@cite{\@for\@citeb:=#1\do
    {\@citea\def\@citea{,\penalty\@citeseppen\ }\@ifundefined
       {b@\@citeb}{{\bf ?}\@warning
       {Citation `\@citeb' on page \thepage \space undefined}}%
{\csname b@\@citeb\endcsname}}}{}}
\def\@citex[#1]#2{\if@filesw\immediate\write\@auxout{\string\citation{#2}}\fi
 \let\@citea\@empty
  \@cite{\@for\@citeb:=#2\do
    {\@citea\def\@citea{;\penalty\@citeseppen\ }%
     \def\@tempa##1##2\@nil{\edef\@citeb{\if##1\space##2\else##1##2\fi}}%
     \expandafter\@tempa\@citeb\@nil
     \@ifundefined{b@\@citeb}{{\bf ?}\@warning
       {Citation `\@citeb' on page \thepage \space undefined}}%
     {\csname b@\@citeb\endcsname}}}{#1}}
%\def\@biblabel#1{\def\citeauthoryear##1##2{##1, ##2}}
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\def\bibfont{\fontsize{9}{11}\selectfont}%
\newdimen\bibindent
\bibindent=1.5em
\def\@biblabel#1{}
\newenvironment{thebibliography}%[1]
     {\section*{\bibname}\bibfont%
      \vspace*{4pt}
      \list{}%
            {\leftmargin2pc%\bibindent
            \itemindent-2pc\labelwidth0pt  %indent for turnlines
        \labelsep0pt  %.33em           %% added by rajesh
            \advance\leftmargin\labelsep
        \itemsep0pt\parsep0pt
            \usecounter{enumiv}%
            \renewcommand\theenumiv{\arabic{enumiv}}}%
      \sloppy\clubpenalty4000\widowpenalty4000%
      \sfcode`\.=\@m}
     {\def\@noitemerr
       {\@latex@warning{Empty `thebibliography' environment}}%
      \endlist}
\newcommand\newblock{}
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Appendix %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\newcounter{appendix}
\newcommand\appendix{\par
  	\refstepcounter{appendix}
	\setcounter{section}{0}%
        \setcounter{lemma}{0}
        \setcounter{theorem}{0}
	\setcounter{definition}{0}
        \setcounter{corollary}{0}
	\setcounter{equation}{0}
	\@addtoreset{equation}{section}
\renewcommand\thesection{\appendixname\ \Alph{section}}
\renewcommand\thesubsection{\Alph{section}.\arabic{subsection}}%
\renewcommand\theequation{\Alph{section}.\arabic{equation}}}%
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%For contents pages %%%%%%%%%%%%%%%%%%%%%%%%
%
\def\journalname{\uppercase{Group 1 Journals}}
\def\No{No.}
\def\chead#1#2#3{\par
\thispagestyle{empty}
{\centering{%
{\titlefont\journalname}\par
{\sl Vol.~#1, \No~#2 (#3)}\par
\vspace*{34pt}
\noindent CONTENTS\par}}
\vspace*{14pt}}
\def\leaderfill{\leaders\hbox to 1em{\hss.\hss}\hfill}
\def\centry#1#2#3{\par
	{\foliofont
	\setbox\tempbox\hbox{#3}
	{\rightskip3.5pc plus1fil
	\noindent{\uppercase{#1}}\par}
	{\leftskip12pt{\rightskip1pc plus1fil
	\ignorespaces\noindent#2\leaderfill\hspace*{2pt}\hskip\wd\tempbox\par}\par}\par
	\vskip-\lastskip
	\vskip-\baselineskip
	\hbox to \hsize{\hfill#3}\par}
	\addvspace{8pt plus1pt minus1pt}\par}
%%
\def\cent#1#2#3{\par{\foliofont
	{\rightskip2pc plus1fil
	\noindent\par}
	{\noindent{\uppercase{#1}}\ignorespaces#2\leaderfill\hspace*{2pt}#3\par}}\par
	\addvspace{8pt plus1pt minus1pt}\par
	}
%
\def\ehead#1#2#3{\par
	\addvspace{12pt plus1pt minus1pt}
	{\foliofont\rightskip4pc plus1fil
	\noindent{\bf #1{#2}{#3}\par}
	\vspace*{4pt}}\par}
%
\def\eehead#1#2#3{\par
	\addvspace{12pt plus1pt minus1pt}
	{\foliofont\rightskip4pc plus1fil
	\noindent{\bf #1{#2}{#3}\par}
	\vspace*{4pt}}\par}
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%Trim Marks %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\newcommand\today{\ifcase\month\or
  January\or February\or March\or April\or May\or June\or
  July\or August\or September\or October\or November\or December\fi
	\space\number\day, \number\year}
\newcount\minute
\newcount\hour
\def\currenttime{%
	\minute\time
	\hour\minute
	\divide\hour60
	\the\hour:\multiply\hour60\advance\minute-\hour\the\minute}
%
%
\def\wsdraftnote{\today\quad\currenttime\qquad\qquad\jobname}%
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\def\cropmarks{\nointerlineskip%
     \vbox to 0pt{\vskip-8.6pt
	\parindent0pt\hspace*{6pt}\wsdraftnote
     \par\advance\trimheight by 2pc
     \vbox to \trimheight{\offinterlineskip\parindent0pt\vskip-2pc
     \hbox to \trimwidth{\raise2.6pc\hbox{\vrule height0pc width0pt}\raisebox{2pc}
   {\hspace*{-2.6pc}\vrule width0pc height0pt}\hfill\raisebox{2pc}
   {\vrule width0pc height0pt}\hspace*{-2.6pc}\raise2.6pc\hbox{\vrule height0pc width0pt}}\vfill
     \hbox to \trimwidth{\lower1.2pc\hbox{\vrule height0pc width0pt}\raisebox{1.4pc}
        {\hspace*{-2.6pc}\vrule width0pc height0pt}\hfill
    \lower1.2pc\hbox{\vrule height0pc width0pt}\rlap{\hspace*{0.6pc}\raisebox{1.4pc}{\vrule width0pc height0pt}}}}}
     \vbox to 0pt{\offinterlineskip\parindent0pt\vskip\topmargin%\vskip1.3pt
     \tempdimen\normaltextheight
     \advance\tempdimen24pt
     \moveright\@themargin
     \vbox to \tempdimen{\hrule height\wsdraftrule
     \vbox to 0pt{\vskip\headheight\vskip\headsep%\vskip3pt
                \vrule height\wsdraftrule width\textwidth}%
      \hbox to \textwidth{\vrule width\wsdraftrule \hfill\vrule height\tempdimen width\wsdraftrule}%
           \hrule height\wsdraftrule}}}%%
\def\xcropmarks{\nointerlineskip%
     \vbox to 0pt{\vskip-8.6pt
	\parindent0pt\hspace*{6pt}\wsdraftnote
     \par\advance\trimheight by 2pc
     \vbox to \trimheight{\offinterlineskip\parindent0pt\vskip-2pc
     \hbox to \trimwidth{\raise2.6pc\hbox{\vrule height0pc width0pt}\raisebox{2pc}
   {\hspace*{-2.6pc}\vrule width0pc height0pt}\hfill\raisebox{2pc}
   {\vrule width0pc height0pt}\hspace*{-2.6pc}\raise2.6pc\hbox{\vrule height0pc width0pt}}\vfill
     \hbox to \trimwidth{\lower1.2pc\hbox{\vrule height0pc width0pt}\raisebox{1.4pc}
        {\hspace*{-2.6pc}\vrule width0pc height0pt}\hfill
    \lower1.2pc\hbox{\vrule height0pc width0pt}\rlap{\hspace*{0.6pc}\raisebox{1.4pc}{\vrule width0pc height0pt}}}}}
     \vbox to 0pt{\offinterlineskip\parindent0pt\vskip\topmargin%\vskip1.3pt
     \tempdimen\normaltextheight
     \advance\tempdimen27pt
     \moveright\@themargin
     \vbox to \tempdimen{\hrule height\wsdraftrule
     \vbox to 0pt{\vskip\headheight\vskip\headsep%\vskip3pt
                \vrule height\wsdraftrule width\textwidth}%
      \hbox to \textwidth{\vrule width\wsdraftrule \hfill\vrule height\tempdimen width\wsdraftrule}%
           \hrule height\wsdraftrule}}}%%
%
\let\trimmarks\cropmarks
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%% Output Routine %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
\def\@outputpage{%
\begingroup           % the \endgroup is put in by \aftergroup
  \let \protect \noexpand
  \@resetactivechars
  \let\-\@dischyph
  \let\'\@acci\let\`\@accii\let\=\@acciii
  \let\\\@normalcr
  \let\par\@@par          %% 15 Sep 87
  \shipout \vbox{%
    \set@typeset@protect
    \aftergroup \endgroup
    \aftergroup \set@typeset@protect
                                % correct? or just restore by ending
                                % the group?
  \if@specialpage
    \global\@specialpagefalse\@nameuse{ps@\@specialstyle}%
  \fi
  \if@twoside
    \ifodd\count\z@ \let\@thehead\@oddhead \let\@thefoot\@oddfoot
         \let\@themargin\oddsidemargin
    \else \let\@thehead\@evenhead
       \let\@thefoot\@evenfoot \let\@themargin\evensidemargin
    \fi
  \fi
  \reset@font
  \normalsize
  \baselineskip\z@skip \lineskip\z@skip \lineskiplimit\z@
    \@begindvi\trimmarks
    \vskip \topmargin
    \moveright\@themargin \vbox {%
      \setbox\@tempboxa \vbox to\headheight{%
        \vfil
        \color@hbox
          \normalcolor
          \hb@xt@\textwidth {%
            \let \label \@gobble
            \let \index \@gobble
            \let \glossary \@gobble %% 21 Jun 91
            \@thehead
            }%
        \color@endbox
        }%                        %% 22 Feb 87
      \dp\@tempboxa \z@
      \box\@tempboxa
      \vskip \headsep
      \box\@outputbox
      \baselineskip \footskip
      \color@hbox
        \normalcolor
        \hb@xt@\textwidth{%
          \let \label \@gobble
          \let \index \@gobble      %% 22 Feb 87
          \let \glossary \@gobble   %% 21 Jun 91
          \@thefoot
          }%
      \color@endbox
      }%
    }%
\global \@colht \textheight
\stepcounter{page}%
\let\firstmark\botmark
}

%
%%%%%%%%%%%%%%%%%%%%% Local Defs. %%%%%%%%%%%%%%%%%%%%%%
%
\def\mtb{\fboxsep=0pt\fbox{\phantom{e}}}
\def\breakhere{\par\vskip-\lastskip
			\pagebreak}
\def\forcebreak{\vadjust{\pagebreak}}
%
\def\and{\hbox{\lowercase{and }}}
\def\aand{\\[10pt]{\upshape{and}}\\[-3pt]}
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%Process Options %%%%%%%%%%%%%%%%%%%%%%%%
%
\pagestyle{headings}
\pagenumbering{arabic}
\onecolumn
\frenchspacing
\flushbottom
\def\sloppy{\tolerance=100000\hfuzz=\maxdimen \vfuzz=\maxdimen}
\sloppy
\vbadness=12000
\hbadness=12000
\RequirePackage{amsfonts}
\RequirePackage{amssymb}
\RequirePackage{amsmath}
\RequirePackage{graphicx}
\endinput
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%End of file%%%%%%%%%%%%%%%%%%%%%%%%%%%%
