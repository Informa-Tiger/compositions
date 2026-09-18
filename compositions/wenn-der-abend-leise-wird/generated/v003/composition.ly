\version "2.26.0"
\pointAndClickOff
\header {
title = "Wenn der Abend leise wird"
subtitle = "Choral fantasia on Es wird scho glei dumpa"
composer = "New composition: Codex (2026)"
poet = "Tune: Anton Reidinger (1839–1912)"
tagline = "Cantus firmus: soprano, mm. 8 (beat 3)–28; tenor, mm. 36 (beat 3)–44."
}
#(set-global-staff-size 16.5)
\paper { #(set-paper-size "a4") top-margin = 12\mm bottom-margin = 12\mm left-margin = 14\mm right-margin = 12\mm system-system-spacing.basic-distance = #17 score-system-spacing.basic-distance = #16 print-page-number = ##t }
global = { \key g \major \time 3/4 }
voiceA = { \global \clef treble
\tempo "Andante, con moto" 4 = 88
\mark \markup { \small "I. Praeambulum" }
r2. |
r2. |
r2. |
r2. |
\break
g'4 g'4 a'4 |
b'8 d''8 d''4. c''8 |
\tempo  4 = 86
b'4 a'4 g'4 |
fis'4 e'4 d'4 |
\break
\tempo  4 = 88
\mark \markup { \small "II. Cantus in soprano" }
g'4 g'4 a'4 |
b'8 d''8 d''4. c''8 |
b'4 b'4 a'4 |
\tempo  4 = 85
g'2 d'4 |
\break
\tempo  4 = 88
g'4 g'4 a'4 |
b'8 d''8 d''4. c''8 |
b'4 b'4 a'4 |
\tempo  4 = 85
g'2 d''4 |
\pageBreak
\tempo  4 = 88
d''4 b'4 d''4 |
d''8 c''8 a'4. c''8 |
b'4 g'4 b'4 |
\tempo  4 = 84
a'2 d'4 |
\break
\tempo  4 = 88
g'4 g'4 a'4 |
b'8 d''8 d''4. c''8 |
b'4 b'4 a'4 |
\tempo  4 = 84
g'2 c''8 fis'8 |
\break
\tempo  4 = 86
g'2 a'8 d'8 |
g'2 g'8 b'8 |
d''4 b'8 g'8 a'8 d'8 |
\tempo  4 = 80
g'2 fis'8 e'8 |
\break
\tempo  4 = 90
\mark \markup { \small "III. Ombra" }
g'8 fis'8 e'4 fis'4 |
g'4 b'8 a'8 g'8 fis'8 |
e'4 e'4 fis'4 |
g'8 b'8 b'4 a'8 g'8 |
\pageBreak
e''8 d''8 c''4 d''4 |
b'4 a'8 g'8 fis'4 |
\tempo  4 = 86
e'8 fis'8 g'2 |
\tempo  4 = 81
fis'4 e'4 fis'4 |
\break
\tempo  4 = 88
\mark \markup { \small "IV. Cantus in tenor" }
g'8 a'8 g'4 fis'4 |
b'4 a'8 g'8 a'4 |
b'8 a'8 g'4 fis'4 |
\tempo  4 = 84
b'8 a'8 g'4 g'4 |
\break
\tempo  4 = 88
b'8 a'8 g'4 c''4 |
d''4 b'8 a'8 a'4 |
b'8 a'8 g'4 fis'4 |
\tempo  4 = 82
g'2 a'8 b'8 |
\break
\tempo  4 = 80
\mark \markup { \small "V. Abendsegen" }
c''4 b'8 a'8 g'4 ~ |
\tempo  4 = 76
g'4 fis'4 a'4 |
\tempo  4 = 69
g'2. ~ |
\tempo  4 = 60
g'2.\fermata |
\break
\bar "|." }
voiceB = { \global \clef treble
r2. |
r2. |
d'4 d'4 e'4 |
fis'8 a'8 a'4. fis'8 |
d'4 e'8 d'8 c'4 |
d'4 g'4 fis'4 |
g'4 c'4 e'4 |
d'4 a4 c'4 |
b4 e'8 d'8 e'4 |
g'2 fis'4 |
g'4 fis'4 fis'4 |
d'2 b4 ~ |
b8 c'8 b4 c'4 |
d'4 fis'4 e'4 |
d'4 g'4 fis'4 |
d'4 e'4 fis'4 |
g'4 fis'8 e'8 fis'4 ~ |
fis'8 e'4. fis'4 |
g'4 e'2 |
e'4 cis'8 d'8 c'4 |
b2 c'4 |
d'4 g'4 fis'4 |
g'4 g'8 fis'8 fis'4 |
d'2. ~ |
d'4 e'8 d'8 c'4 |
b4 c'8 b8 d'4 ~ |
d'4 e'4 c'4 |
b2. ~ |
b8 c'8 b4 dis'4 |
e'8 d'8 e'8 fis'8 e'4 |
c'2 dis'4 |
e'8 g'8 d'4 e'4 |
e'2 fis'4 |
d'4 c'4 d'4 |
c'4 d'4 cis'4 |
d'4 c'2 |
b4 e'4 d'4 |
d'4 fis'2 |
g'4 fis'8 e'8 d'4 ~ |
d'4 e'8 d'8 b4 |
e'2. |
g'4 fis'8 e'8 fis'4 |
g'4 fis'8 e'8 d'4 ~ |
d'2 fis'4 |
g'4 e'4 e'4 |
d'2 c'4 |
b2 e'4 |
d'2.\fermata |
\bar "|." }
voiceC = { \global \clef bass
g4 g4 a4 |
b8 d'8 d'4. c'8 |
b8 a8 g4 c'4 |
d'4 c'8 b8 a4 |
b4 e4 a4 |
g8 a8 b4 a4 |
g4 e2 |
fis2 a4 |
g2 c'4 |
g8 a8 b4 a4 |
d'4. c'8 d'4 |
b8 a8 g8 fis8 g4 ~ |
g4 e2 |
g4 fis8 a8 g4 |
g8 b8 d'4 a8 d'8 |
b4 g4 a4 |
b4 d'4 a4 ~ |
a8 g8 e4 a4 |
g2. |
a4 g4 fis4 |
g8 fis8 g4 e4 |
g4 b8 a8 a4 |
d'4. c'8 d'4 |
b2 a4 |
b2 fis4 |
g8 a8 b8 a8 g8 a8 |
b2 fis4 |
g4 a8 g8 g4 ~ |
g2 a4 |
g4 c'4 a4 ~ |
a2. |
g2 e4 |
g4 b8 a8 a4 |
g4 e4 a4 |
g2 e4 |
fis4 g4 d4 |
g4 g4 a4 |
b8 d'8 d'4. c'8 |
b4 b4 a4 |
g2 d4 |
g4 g4 a4 |
b8 d'8 d'4. c'8 |
b4 b4 a4 |
g2 d'4 |
e'8 d'8 c'2 |
b4 a4 fis4 |
g2. |
b2.\fermata |
\bar "|." }
voiceD = { \global \clef bass
r2. |
r2. |
r2. |
r2. |
r2. |
r2. |
g,4 a,4 c4 |
d2. |
g,4 c4 a,4 |
g,2 d4 |
g,4 b,4 d4 |
g,8 a,8 b,4 b,4 |
e,2 a,4 |
g,4 a,4 c4 |
g,4 b,4 d4 |
g,8 b,8 c4 d,4 |
g,4 b,4 d,4 |
d8 e8 c4 d,4 |
g,4 c4 e,4 |
c4 a,4 d4 |
g,4 e,4 a,4 |
g,2 d4 |
g,4 b,4 d4 |
g,2 d4 |
g,4 e4 d4 |
g,4 e,4 b,4 |
b,4 g,4 d4 |
g,2 e4 |
e2 b,4 |
e4 a,4 c4 |
c2 b,4 |
e4 g,4 c4 |
c2 d,4 |
g,4 a,4 d,4 |
c4 e4 a,4 |
d,4 e,4 d,4 |
e,4 c4 d,4 |
g,4 d2 |
g,4 e,4 d4 |
g,2 b,4 |
e,2 a,4 |
g,4 d2 |
g,4 e,4 d4 |
g,2 d,4 |
c4 c4 c4 |
d2. |
g,2 c4 |
g,2.\fermata |
\bar "|." }
\score { \new StaffGroup <<
\new Staff \with { instrumentName = "Soprano" shortInstrumentName = "S." } \voiceA
\new Staff \with { instrumentName = "Alto" shortInstrumentName = "A." } \voiceB
\new Staff \with { instrumentName = "Tenor" shortInstrumentName = "T." } \voiceC
\new Staff \with { instrumentName = "Bass" shortInstrumentName = "B." } \voiceD
>> \layout { indent = 14\mm short-indent = 7\mm \context { \Score \override RehearsalMark.self-alignment-X = #LEFT } } }
