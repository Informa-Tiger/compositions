import Std

/-!
Finite, kernel-evaluated counterpoint checks for independently timed SATB.
Time and duration use caller-chosen integer ticks; MIDI pitches are Nat.
Rests are absences of notes, not pitch zero. Voices may enter, leave, sustain,
and attack independently. Every check is explicitly limited to this model.
No axiom, sorry, native_decide, generated proof oracle, or listening claim.
-/
namespace Counterpoint

/-- Configuration is data, checked by `validConfig`; no tune or key is built in.
The four ranges/maxLeaps are SATB ordered. maxLeaps is validated here but the
maximum-leap rule itself belongs to the separate Python audit. -/
structure Config where
  totalTicks : Nat
  ticksPerQuarter : Nat
  tonicPc : Nat
  tonicThird : Nat
  allowedPcs : List Nat
  ranges : List (Nat × Nat)
  maxLeaps : List Nat
  pulseStride : Nat
  pulseOffset : Nat
  tritoneMaxWait : Nat
  requireIndependence : Bool
  minIndependentChanges : Nat
  deriving DecidableEq, Repr

def validConfig (c : Config) : Bool :=
  c.totalTicks > 0 && c.ticksPerQuarter > 0 && c.tonicPc < 12 &&
  (c.tonicThird == 3 || c.tonicThird == 4) &&
  !c.allowedPcs.isEmpty && c.allowedPcs.all (fun p => p < 12) &&
  c.ranges.length == 4 && c.ranges.all (fun (lo, hi) => 0 < lo && lo ≤ hi && hi < 128) &&
  c.maxLeaps.length == 4 && c.maxLeaps.all (fun n => n > 0) &&
  c.pulseStride > 0 && c.pulseOffset < c.pulseStride &&
  c.tritoneMaxWait > 0 && c.minIndependentChanges > 0

structure Note where
  start : Nat
  dur : Nat
  pitch : Nat
  deriving DecidableEq, Repr

structure Voices where
  s : List Note
  a : List Note
  t : List Note
  b : List Note
  deriving DecidableEq, Repr

structure Frame where
  s : Option Nat
  a : Option Nat
  t : Option Nat
  b : Option Nat
  deriving DecidableEq, Repr

def voiceLists (v : Voices) : List (List Note) := [v.s, v.a, v.t, v.b]
def pitches (f : Frame) : List (Option Nat) := [f.s, f.a, f.t, f.b]
def soundingPitches (f : Frame) : List Nat := (pitches f).filterMap id

def activeAt (n : Note) (tick : Nat) : Bool :=
  n.start ≤ tick && tick < n.start + n.dur

def soundingAt (ns : List Note) (tick : Nat) : Option Nat :=
  (ns.find? (fun n => activeAt n tick)).map Note.pitch

def frameAt (v : Voices) (tick : Nat) : Frame :=
  ⟨soundingAt v.s tick, soundingAt v.a tick,
   soundingAt v.t tick, soundingAt v.b tick⟩

def timeline (v : Voices) (totalTicks : Nat) : List Frame :=
  (List.range totalTicks).map (frameAt v)

def orderedNonoverlapping : List Note → Bool
  | [] => true
  | [_] => true
  | x :: y :: rest => x.start + x.dur ≤ y.start && orderedNonoverlapping (y :: rest)

def wellFormedVoice (ns : List Note) (totalTicks : Nat) : Bool :=
  !ns.isEmpty && orderedNonoverlapping ns &&
    ns.all (fun n => n.dur > 0 && n.pitch > 0 && n.pitch < 128 &&
      n.start + n.dur ≤ totalTicks)

def wellFormed (v : Voices) (totalTicks : Nat) : Bool :=
  totalTicks > 0 && (voiceLists v).all (fun ns => wellFormedVoice ns totalTicks)

-- Exported frame data may be independently compared with this derived timeline.
def frameDataAgrees (v : Voices) (totalTicks : Nat) (exported : List Frame) : Bool :=
  exported == timeline v totalTicks

def distance (p q : Nat) : Nat := p - q + (q - p)
def octaveClass (p q : Nat) : Bool := distance p q % 12 == 0
def fifthClass (p q : Nat) : Bool := distance p q % 12 == 7
def perfectClass (p q : Nat) : Bool := octaveClass p q || fifthClass p q

def sameDirection (p p' q q' : Nat) : Bool :=
  (p < p' && q < q') || (p' < p && q' < q)

def directPerfect (u l u' l' : Nat) : Bool :=
  sameDirection u u' l l' && perfectClass u' l'

def parallelPerfect (u l u' l' : Nat) : Bool :=
  sameDirection u u' l l' &&
    ((octaveClass u l && octaveClass u' l') ||
      (fifthClass u l && fifthClass u' l'))

-- Conservative project-policy battuta definition:
-- inward contrary motion into octave/unison class, for any voice pair.
def battuta (u l u' l' : Nat) : Bool :=
  u' < u && l < l' && octaveClass u' l'

def absentOrSafe (bad : Nat → Nat → Nat → Nat → Bool)
    (u l u' l' : Option Nat) : Bool :=
  match u with
  | none => true
  | some a => match l with
    | none => true
    | some b => match u' with
      | none => true
      | some c => match l' with
        | none => true
        | some d => !(bad a b c d)

def allPairsSafe (bad : Nat → Nat → Nat → Nat → Bool) (x y : Frame) : Bool :=
  absentOrSafe bad x.s x.a y.s y.a &&
  absentOrSafe bad x.s x.t y.s y.t &&
  absentOrSafe bad x.s x.b y.s y.b &&
  absentOrSafe bad x.a x.t y.a y.t &&
  absentOrSafe bad x.a x.b y.a y.b &&
  absentOrSafe bad x.t x.b y.t y.b

def checkTransitions (rule : Frame → Frame → Bool) : List Frame → Bool
  | [] => true
  | [_] => true
  | x :: y :: rest => rule x y && checkTransitions rule (y :: rest)

def checkNoDirect (fs : List Frame) : Bool :=
  checkTransitions (allPairsSafe directPerfect) fs

def checkNoParallel (fs : List Frame) : Bool :=
  checkTransitions (allPairsSafe parallelPerfect) fs

def checkNoBattuta (fs : List Frame) : Bool :=
  checkTransitions (allPairsSafe battuta) fs

-- A second audit on an explicitly declared slower pulse prevents merely
-- displacing one voice by a tick from hiding a direct-perfect progression.
def sampledTimeline (v : Voices) (totalTicks stride offset : Nat) : List Frame :=
  ((List.range totalTicks).filter (fun tick => stride > 0 && tick % stride == offset)).map
    (frameAt v)

def checkStructural (v : Voices) (totalTicks stride offset : Nat) : Bool :=
  let fs := sampledTimeline v totalTicks stride offset
  stride > 0 && offset < stride && checkNoDirect fs && checkNoParallel fs && checkNoBattuta fs

-- Additional mandatory test for alternating displaced attacks. First discard
-- frames where neither member of a pair changes; then examine triples where
-- the upper voice moves alone followed by the lower alone, or vice versa.
-- The combined motion may not conceal a direct perfect or inward octave.
def compressPairTrace : List (Option Nat × Option Nat) → List (Option Nat × Option Nat)
  | [] => []
  | [x] => [x]
  | x :: y :: rest =>
    if x == y then compressPairTrace (y :: rest)
    else x :: compressPairTrace (y :: rest)

def alternatingStagger (x y z : Option Nat × Option Nat) : Bool :=
  ((x.1 != y.1 && x.2 == y.2 && y.1 == z.1 && y.2 != z.2) ||
   (x.1 == y.1 && x.2 != y.2 && y.1 != z.1 && y.2 == z.2)) &&
  (!(absentOrSafe directPerfect x.1 x.2 z.1 z.2) ||
   !(absentOrSafe battuta x.1 x.2 z.1 z.2))

def safeStaggers : List (Option Nat × Option Nat) → Bool
  | [] => true
  | [_] => true
  | [_, _] => true
  | x :: y :: z :: rest =>
    !alternatingStagger x y z && safeStaggers (y :: z :: rest)

def pairStaggersSafe (fs : List Frame) (upper lower : Frame → Option Nat) : Bool :=
  safeStaggers (compressPairTrace (fs.map (fun f => (upper f, lower f))))

def checkNoStaggeredPerfects (fs : List Frame) : Bool :=
  pairStaggersSafe fs Frame.s Frame.a && pairStaggersSafe fs Frame.s Frame.t &&
  pairStaggersSafe fs Frame.s Frame.b && pairStaggersSafe fs Frame.a Frame.t &&
  pairStaggersSafe fs Frame.a Frame.b && pairStaggersSafe fs Frame.t Frame.b

def noCrossedPair (upper lower : Option Nat) : Bool :=
  match upper with
  | none => true
  | some u => match lower with
    | none => true
    | some l => l ≤ u

def noCrossing (f : Frame) : Bool :=
  noCrossedPair f.s f.a && noCrossedPair f.s f.t && noCrossedPair f.s f.b &&
  noCrossedPair f.a f.t && noCrossedPair f.a f.b && noCrossedPair f.t f.b

def inRange (lo hi : Nat) (p : Option Nat) : Bool :=
  match p with
  | none => true
  | some n => lo ≤ n && n ≤ hi

def voiceRanges (c : Config) (f : Frame) : Bool :=
  (c.ranges.zip (pitches f)).all (fun ((lo, hi), p) => inRange lo hi p)

def inScale (c : Config) (f : Frame) : Bool :=
  (soundingPitches f).all (fun p => c.allowedPcs.contains (p % 12))

def melodicPair (x y : Note) : Bool :=
  -- A rest genuinely breaks the melodic continuity obligation; a repeated
  -- articulation without a rest does not. Compound tritones are also excluded.
  x.start + x.dur < y.start || distance x.pitch y.pitch % 12 != 6

def checkMelodicVoice : List Note → Bool
  | [] => true
  | [_] => true
  | x :: y :: rest => melodicPair x y && checkMelodicVoice (y :: rest)

def checkMelody (v : Voices) : Bool := (voiceLists v).all checkMelodicVoice

def hasHarmonicTritone (f : Frame) : Bool :=
  (soundingPitches f).any (fun p =>
    (soundingPitches f).any (fun q => distance p q % 12 == 6))

def hasExactlyPCs (f : Frame) (pcs : List Nat) : Bool :=
  let actual := (soundingPitches f).map (· % 12)
  actual.all pcs.contains && pcs.all actual.contains

/-- A strict tonic-relative dominant seventh in first inversion:
all four chord pitch classes must occur, with the leading tone in the bass. -/
def isV65 (c : Config) (f : Frame) : Bool :=
  f.b.any (fun p => p % 12 == (c.tonicPc + 11) % 12) &&
  hasExactlyPCs f ([11, 2, 5, 7].map (fun p => (c.tonicPc + p) % 12))

def isRootTonic53 (c : Config) (f : Frame) : Bool :=
  f.b.any (fun p => p % 12 == c.tonicPc) &&
  hasExactlyPCs f ([0, c.tonicThird, 7].map (fun p => (c.tonicPc + p) % 12))

-- The dominant seventh (tonic+5) descends to the major/minor tonic third;
-- the leading tone (tonic+11) ascends by a semitone. No voice exchange.
def resolvesCriticalPitch (c : Config) (p q : Option Nat) : Bool :=
  match p with
  | none => true
  | some n =>
    if n % 12 == (c.tonicPc + 5) % 12 then q == some (n - (5 - c.tonicThird))
    else if n % 12 == (c.tonicPc + 11) % 12 then q == some (n + 1)
    else true

def resolvesV65 (c : Config) (x y : Frame) : Bool :=
  isV65 c x && isRootTonic53 c y &&
  resolvesCriticalPitch c x.s y.s && resolvesCriticalPitch c x.a y.a &&
  resolvesCriticalPitch c x.t y.t && resolvesCriticalPitch c x.b y.b

def heldCriticalPitch (c : Config) (p q : Option Nat) : Bool :=
  match p with
  | none => true
  | some n =>
    if n % 12 == (c.tonicPc + 5) % 12 || n % 12 == (c.tonicPc + 11) % 12
    then q == p else true

def criticalPitchesHeld (c : Config) (origin next : Frame) : Bool :=
  heldCriticalPitch c origin.s next.s && heldCriticalPitch c origin.a next.a &&
  heldCriticalPitch c origin.t next.t && heldCriticalPitch c origin.b next.b

def resolvesV65Within (c : Config) (origin : Frame) : Nat → List Frame → Bool
  | 0, _ => false
  | _ + 1, [] => false
  | wait + 1, next :: rest =>
    resolvesV65 c origin next ||
    (criticalPitchesHeld c origin next && resolvesV65Within c origin wait rest)

/-- Each sounding tritone independently requires a complete V65 -> tonic 53
within the configured number of ticks. All critical notes keep their exact
pitch in their original voice until a common resolution. Early resolution,
departure-and-return, revoicing, intervening rests, and late resolution fail.
This is a deliberately narrow project policy, not universal historical law. -/
def checkTritones (c : Config) : List Frame → Bool
  | [] => true
  | x :: rest =>
    (!hasHarmonicTritone x ||
      (isV65 c x && resolvesV65Within c x c.tritoneMaxWait rest)) &&
    checkTritones c rest

def hasOnsetAt (ns : List Note) (tick : Nat) : Bool :=
  ns.any (fun n => n.start == tick)

def hasSustainAcross (ns : List Note) (tick : Nat) : Bool :=
  ns.any (fun n => n.start < tick && tick < n.start + n.dur)

def hasPitchChangeAt (ns : List Note) (tick : Nat) : Bool :=
  tick > 0 && hasOnsetAt ns tick &&
  match soundingAt ns (tick - 1) with
  | none => false
  | some p => match soundingAt ns tick with
    | none => false
    | some q => p != q

-- Counts real pitch-changing attacks in this voice while another voice is
-- inside a held note. Tied notation/rearticulation does not manufacture it.
def independentChangeCount (ns other : List Note) (totalTicks : Nat) : Nat :=
  ((List.range totalTicks).filter (fun tick =>
    hasPitchChangeAt ns tick && hasSustainAcross other tick)).length

def voiceHasIndependence (ns : List Note) (all : List (List Note))
    (totalTicks threshold : Nat) : Bool :=
  all.any (fun other => independentChangeCount ns other totalTicks ≥ threshold)

def hasRhythmicIndependence (c : Config) (v : Voices) : Bool :=
  (voiceLists v).all (fun ns =>
    voiceHasIndependence ns (voiceLists v) c.totalTicks c.minIndependentChanges)

-- Entry/reentry means a positive gap before a later note, independently of
-- engraving rests. Expose separately instead of assuming every piece has one.
def hasReentry : List Note → Bool
  | [] => false
  | [_] => false
  | x :: y :: rest => x.start + x.dur < y.start || hasReentry (y :: rest)

-- Exact transposition preserves the subject's pitches, inter-onset rhythm,
-- and note durations. The witness specifies the literal matching passage.
def subjectAt (subject passage : List Note) (timeShift : Nat) (pitchShift : Int) : Bool :=
  subject.length == passage.length &&
  (subject.zip passage).all (fun (x, y) =>
    y.start == x.start + timeShift && y.dur == x.dur &&
    (y.pitch : Int) == (x.pitch : Int) + pitchShift)

/-- The complete formal acceptance predicate. In particular, malformed
configuration/score data cannot make the individual checks vacuously pass.
Pulse checking and stagger checking are mandatory under this policy.
Maximum melodic leaps and any compositional cost function are NOT certified. -/
def certified (c : Config) (v : Voices) : Bool :=
  let fs := timeline v c.totalTicks
  validConfig c && wellFormed v c.totalTicks &&
  checkNoDirect fs && checkNoParallel fs && checkNoBattuta fs &&
  checkStructural v c.totalTicks c.pulseStride c.pulseOffset &&
  checkNoStaggeredPerfects fs &&
  fs.all noCrossing && fs.all (voiceRanges c) && fs.all (inScale c) &&
  checkMelody v && checkTritones c fs &&
  (!c.requireIndependence || hasRhythmicIndependence c v)

end Counterpoint


-- Generated from audited input; run Lean to verify.
set_option maxRecDepth 100000
set_option maxHeartbeats 0
namespace Certificate
open Counterpoint

def config : Config := {
  totalTicks := 24
  ticksPerQuarter := 2
  tonicPc := 9
  tonicThird := 3
  pulseStride := 2
  pulseOffset := 0
  tritoneMaxWait := 2
  minIndependentChanges := 2
  allowedPcs := [9, 11, 0, 2, 4, 5, 8]
  ranges := [(64, 76), (57, 69), (49, 64), (37, 52)]
  maxLeaps := [7, 7, 7, 12]
  requireIndependence := true
}

def voices : Voices := {
  s := [⟨0, 4, 69⟩,
    ⟨4, 4, 71⟩,
    ⟨8, 4, 72⟩,
    ⟨12, 4, 71⟩,
    ⟨16, 4, 69⟩,
    ⟨20, 4, 69⟩]
  a := [⟨0, 1, 64⟩,
    ⟨1, 2, 65⟩,
    ⟨3, 6, 64⟩,
    ⟨9, 2, 60⟩,
    ⟨11, 6, 64⟩,
    ⟨17, 2, 60⟩,
    ⟨19, 2, 57⟩,
    ⟨21, 3, 60⟩]
  t := [⟨0, 2, 57⟩,
    ⟨2, 2, 60⟩,
    ⟨4, 1, 59⟩,
    ⟨5, 3, 56⟩,
    ⟨8, 9, 52⟩,
    ⟨17, 3, 53⟩,
    ⟨20, 4, 52⟩]
  b := [⟨0, 1, 48⟩,
    ⟨1, 3, 45⟩,
    ⟨4, 4, 44⟩,
    ⟨8, 4, 45⟩,
    ⟨12, 4, 44⟩,
    ⟨16, 1, 48⟩,
    ⟨17, 3, 45⟩,
    ⟨20, 1, 48⟩,
    ⟨21, 3, 45⟩]
}

theorem config_valid : validConfig config = true := by decide
theorem accepted : certified config voices = true := by decide

#print axioms config_valid
#print axioms accepted
end Certificate
