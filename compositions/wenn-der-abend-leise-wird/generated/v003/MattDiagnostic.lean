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

-- Diagnostic proof: unchanged Matt predicates; failures are proved false, not waived.
set_option maxRecDepth 100000
set_option maxHeartbeats 0
namespace Review
open Counterpoint
def config : Config := {
  totalTicks := 288
  ticksPerQuarter := 2
  tonicPc := 7
  tonicThird := 4
  pulseStride := 2
  pulseOffset := 0
  tritoneMaxWait := 2
  minIndependentChanges := 1
  allowedPcs := [0, 2, 4, 6, 7, 9, 11]
  ranges := [(60, 84), (55, 77), (48, 69), (36, 64)]
  maxLeaps := [7, 7, 7, 12]
  requireIndependence := true
}
def voices : Voices := {
  s := [⟨24, 2, 67⟩, ⟨26, 2, 67⟩, ⟨28, 2, 69⟩, ⟨30, 1, 71⟩, ⟨31, 1, 74⟩, ⟨32, 3, 74⟩, ⟨35, 1, 72⟩, ⟨36, 2, 71⟩, ⟨38, 2, 69⟩, ⟨40, 2, 67⟩, ⟨42, 2, 66⟩, ⟨44, 2, 64⟩, ⟨46, 2, 62⟩, ⟨48, 2, 67⟩, ⟨50, 2, 67⟩, ⟨52, 2, 69⟩, ⟨54, 1, 71⟩, ⟨55, 1, 74⟩, ⟨56, 3, 74⟩, ⟨59, 1, 72⟩, ⟨60, 2, 71⟩, ⟨62, 2, 71⟩, ⟨64, 2, 69⟩, ⟨66, 4, 67⟩, ⟨70, 2, 62⟩, ⟨72, 2, 67⟩, ⟨74, 2, 67⟩, ⟨76, 2, 69⟩, ⟨78, 1, 71⟩, ⟨79, 1, 74⟩, ⟨80, 3, 74⟩, ⟨83, 1, 72⟩, ⟨84, 2, 71⟩, ⟨86, 2, 71⟩, ⟨88, 2, 69⟩, ⟨90, 4, 67⟩, ⟨94, 2, 74⟩, ⟨96, 2, 74⟩, ⟨98, 2, 71⟩, ⟨100, 2, 74⟩, ⟨102, 1, 74⟩, ⟨103, 1, 72⟩, ⟨104, 3, 69⟩, ⟨107, 1, 72⟩, ⟨108, 2, 71⟩, ⟨110, 2, 67⟩, ⟨112, 2, 71⟩, ⟨114, 4, 69⟩, ⟨118, 2, 62⟩, ⟨120, 2, 67⟩, ⟨122, 2, 67⟩, ⟨124, 2, 69⟩, ⟨126, 1, 71⟩, ⟨127, 1, 74⟩, ⟨128, 3, 74⟩, ⟨131, 1, 72⟩, ⟨132, 2, 71⟩, ⟨134, 2, 71⟩, ⟨136, 2, 69⟩, ⟨138, 4, 67⟩, ⟨142, 1, 72⟩, ⟨143, 1, 66⟩, ⟨144, 4, 67⟩, ⟨148, 1, 69⟩, ⟨149, 1, 62⟩, ⟨150, 4, 67⟩, ⟨154, 1, 67⟩, ⟨155, 1, 71⟩, ⟨156, 2, 74⟩, ⟨158, 1, 71⟩, ⟨159, 1, 67⟩, ⟨160, 1, 69⟩, ⟨161, 1, 62⟩, ⟨162, 4, 67⟩, ⟨166, 1, 66⟩, ⟨167, 1, 64⟩, ⟨168, 1, 67⟩, ⟨169, 1, 66⟩, ⟨170, 2, 64⟩, ⟨172, 2, 66⟩, ⟨174, 2, 67⟩, ⟨176, 1, 71⟩, ⟨177, 1, 69⟩, ⟨178, 1, 67⟩, ⟨179, 1, 66⟩, ⟨180, 2, 64⟩, ⟨182, 2, 64⟩, ⟨184, 2, 66⟩, ⟨186, 1, 67⟩, ⟨187, 1, 71⟩, ⟨188, 2, 71⟩, ⟨190, 1, 69⟩, ⟨191, 1, 67⟩, ⟨192, 1, 76⟩, ⟨193, 1, 74⟩, ⟨194, 2, 72⟩, ⟨196, 2, 74⟩, ⟨198, 2, 71⟩, ⟨200, 1, 69⟩, ⟨201, 1, 67⟩, ⟨202, 2, 66⟩, ⟨204, 1, 64⟩, ⟨205, 1, 66⟩, ⟨206, 4, 67⟩, ⟨210, 2, 66⟩, ⟨212, 2, 64⟩, ⟨214, 2, 66⟩, ⟨216, 1, 67⟩, ⟨217, 1, 69⟩, ⟨218, 2, 67⟩, ⟨220, 2, 66⟩, ⟨222, 2, 71⟩, ⟨224, 1, 69⟩, ⟨225, 1, 67⟩, ⟨226, 2, 69⟩, ⟨228, 1, 71⟩, ⟨229, 1, 69⟩, ⟨230, 2, 67⟩, ⟨232, 2, 66⟩, ⟨234, 1, 71⟩, ⟨235, 1, 69⟩, ⟨236, 2, 67⟩, ⟨238, 2, 67⟩, ⟨240, 1, 71⟩, ⟨241, 1, 69⟩, ⟨242, 2, 67⟩, ⟨244, 2, 72⟩, ⟨246, 2, 74⟩, ⟨248, 1, 71⟩, ⟨249, 1, 69⟩, ⟨250, 2, 69⟩, ⟨252, 1, 71⟩, ⟨253, 1, 69⟩, ⟨254, 2, 67⟩, ⟨256, 2, 66⟩, ⟨258, 4, 67⟩, ⟨262, 1, 69⟩, ⟨263, 1, 71⟩, ⟨264, 2, 72⟩, ⟨266, 1, 71⟩, ⟨267, 1, 69⟩, ⟨268, 4, 67⟩, ⟨272, 2, 66⟩, ⟨274, 2, 69⟩, ⟨276, 12, 67⟩]
  a := [⟨12, 2, 62⟩, ⟨14, 2, 62⟩, ⟨16, 2, 64⟩, ⟨18, 1, 66⟩, ⟨19, 1, 69⟩, ⟨20, 3, 69⟩, ⟨23, 1, 66⟩, ⟨24, 2, 62⟩, ⟨26, 1, 64⟩, ⟨27, 1, 62⟩, ⟨28, 2, 60⟩, ⟨30, 2, 62⟩, ⟨32, 2, 67⟩, ⟨34, 2, 66⟩, ⟨36, 2, 67⟩, ⟨38, 2, 60⟩, ⟨40, 2, 64⟩, ⟨42, 2, 62⟩, ⟨44, 2, 57⟩, ⟨46, 2, 60⟩, ⟨48, 2, 59⟩, ⟨50, 1, 64⟩, ⟨51, 1, 62⟩, ⟨52, 2, 64⟩, ⟨54, 4, 67⟩, ⟨58, 2, 66⟩, ⟨60, 2, 67⟩, ⟨62, 2, 66⟩, ⟨64, 2, 66⟩, ⟨66, 4, 62⟩, ⟨70, 3, 59⟩, ⟨73, 1, 60⟩, ⟨74, 2, 59⟩, ⟨76, 2, 60⟩, ⟨78, 2, 62⟩, ⟨80, 2, 66⟩, ⟨82, 2, 64⟩, ⟨84, 2, 62⟩, ⟨86, 2, 67⟩, ⟨88, 2, 66⟩, ⟨90, 2, 62⟩, ⟨92, 2, 64⟩, ⟨94, 2, 66⟩, ⟨96, 2, 67⟩, ⟨98, 1, 66⟩, ⟨99, 1, 64⟩, ⟨100, 3, 66⟩, ⟨103, 3, 64⟩, ⟨106, 2, 66⟩, ⟨108, 2, 67⟩, ⟨110, 4, 64⟩, ⟨114, 2, 64⟩, ⟨116, 1, 61⟩, ⟨117, 1, 62⟩, ⟨118, 2, 60⟩, ⟨120, 4, 59⟩, ⟨124, 2, 60⟩, ⟨126, 2, 62⟩, ⟨128, 2, 67⟩, ⟨130, 2, 66⟩, ⟨132, 2, 67⟩, ⟨134, 1, 67⟩, ⟨135, 1, 66⟩, ⟨136, 2, 66⟩, ⟨138, 8, 62⟩, ⟨146, 1, 64⟩, ⟨147, 1, 62⟩, ⟨148, 2, 60⟩, ⟨150, 2, 59⟩, ⟨152, 1, 60⟩, ⟨153, 1, 59⟩, ⟨154, 4, 62⟩, ⟨158, 2, 64⟩, ⟨160, 2, 60⟩, ⟨162, 7, 59⟩, ⟨169, 1, 60⟩, ⟨170, 2, 59⟩, ⟨172, 2, 63⟩, ⟨174, 1, 64⟩, ⟨175, 1, 62⟩, ⟨176, 1, 64⟩, ⟨177, 1, 66⟩, ⟨178, 2, 64⟩, ⟨180, 4, 60⟩, ⟨184, 2, 63⟩, ⟨186, 1, 64⟩, ⟨187, 1, 67⟩, ⟨188, 2, 62⟩, ⟨190, 2, 64⟩, ⟨192, 4, 64⟩, ⟨196, 2, 66⟩, ⟨198, 2, 62⟩, ⟨200, 2, 60⟩, ⟨202, 2, 62⟩, ⟨204, 2, 60⟩, ⟨206, 2, 62⟩, ⟨208, 2, 61⟩, ⟨210, 2, 62⟩, ⟨212, 4, 60⟩, ⟨216, 2, 59⟩, ⟨218, 2, 64⟩, ⟨220, 2, 62⟩, ⟨222, 2, 62⟩, ⟨224, 4, 66⟩, ⟨228, 2, 67⟩, ⟨230, 1, 66⟩, ⟨231, 1, 64⟩, ⟨232, 4, 62⟩, ⟨236, 1, 64⟩, ⟨237, 1, 62⟩, ⟨238, 2, 59⟩, ⟨240, 6, 64⟩, ⟨246, 2, 67⟩, ⟨248, 1, 66⟩, ⟨249, 1, 64⟩, ⟨250, 2, 66⟩, ⟨252, 2, 67⟩, ⟨254, 1, 66⟩, ⟨255, 1, 64⟩, ⟨256, 6, 62⟩, ⟨262, 2, 66⟩, ⟨264, 2, 67⟩, ⟨266, 2, 64⟩, ⟨268, 2, 64⟩, ⟨270, 4, 62⟩, ⟨274, 2, 60⟩, ⟨276, 4, 59⟩, ⟨280, 2, 64⟩, ⟨282, 6, 62⟩]
  t := [⟨0, 2, 55⟩, ⟨2, 2, 55⟩, ⟨4, 2, 57⟩, ⟨6, 1, 59⟩, ⟨7, 1, 62⟩, ⟨8, 3, 62⟩, ⟨11, 1, 60⟩, ⟨12, 1, 59⟩, ⟨13, 1, 57⟩, ⟨14, 2, 55⟩, ⟨16, 2, 60⟩, ⟨18, 2, 62⟩, ⟨20, 1, 60⟩, ⟨21, 1, 59⟩, ⟨22, 2, 57⟩, ⟨24, 2, 59⟩, ⟨26, 2, 52⟩, ⟨28, 2, 57⟩, ⟨30, 1, 55⟩, ⟨31, 1, 57⟩, ⟨32, 2, 59⟩, ⟨34, 2, 57⟩, ⟨36, 2, 55⟩, ⟨38, 4, 52⟩, ⟨42, 4, 54⟩, ⟨46, 2, 57⟩, ⟨48, 4, 55⟩, ⟨52, 2, 60⟩, ⟨54, 1, 55⟩, ⟨55, 1, 57⟩, ⟨56, 2, 59⟩, ⟨58, 2, 57⟩, ⟨60, 3, 62⟩, ⟨63, 1, 60⟩, ⟨64, 2, 62⟩, ⟨66, 1, 59⟩, ⟨67, 1, 57⟩, ⟨68, 1, 55⟩, ⟨69, 1, 54⟩, ⟨70, 4, 55⟩, ⟨74, 4, 52⟩, ⟨78, 2, 55⟩, ⟨80, 1, 54⟩, ⟨81, 1, 57⟩, ⟨82, 2, 55⟩, ⟨84, 1, 55⟩, ⟨85, 1, 59⟩, ⟨86, 2, 62⟩, ⟨88, 1, 57⟩, ⟨89, 1, 62⟩, ⟨90, 2, 59⟩, ⟨92, 2, 55⟩, ⟨94, 2, 57⟩, ⟨96, 2, 59⟩, ⟨98, 2, 62⟩, ⟨100, 3, 57⟩, ⟨103, 1, 55⟩, ⟨104, 2, 52⟩, ⟨106, 2, 57⟩, ⟨108, 6, 55⟩, ⟨114, 2, 57⟩, ⟨116, 2, 55⟩, ⟨118, 2, 54⟩, ⟨120, 1, 55⟩, ⟨121, 1, 54⟩, ⟨122, 2, 55⟩, ⟨124, 2, 52⟩, ⟨126, 2, 55⟩, ⟨128, 1, 59⟩, ⟨129, 1, 57⟩, ⟨130, 2, 57⟩, ⟨132, 3, 62⟩, ⟨135, 1, 60⟩, ⟨136, 2, 62⟩, ⟨138, 4, 59⟩, ⟨142, 2, 57⟩, ⟨144, 4, 59⟩, ⟨148, 2, 54⟩, ⟨150, 1, 55⟩, ⟨151, 1, 57⟩, ⟨152, 1, 59⟩, ⟨153, 1, 57⟩, ⟨154, 1, 55⟩, ⟨155, 1, 57⟩, ⟨156, 4, 59⟩, ⟨160, 2, 54⟩, ⟨162, 2, 55⟩, ⟨164, 1, 57⟩, ⟨165, 1, 55⟩, ⟨166, 6, 55⟩, ⟨172, 2, 57⟩, ⟨174, 2, 55⟩, ⟨176, 2, 60⟩, ⟨178, 8, 57⟩, ⟨186, 4, 55⟩, ⟨190, 2, 52⟩, ⟨192, 2, 55⟩, ⟨194, 1, 59⟩, ⟨195, 1, 57⟩, ⟨196, 2, 57⟩, ⟨198, 2, 55⟩, ⟨200, 2, 52⟩, ⟨202, 2, 57⟩, ⟨204, 4, 55⟩, ⟨208, 2, 52⟩, ⟨210, 2, 54⟩, ⟨212, 2, 55⟩, ⟨214, 2, 50⟩, ⟨216, 2, 55⟩, ⟨218, 2, 55⟩, ⟨220, 2, 57⟩, ⟨222, 1, 59⟩, ⟨223, 1, 62⟩, ⟨224, 3, 62⟩, ⟨227, 1, 60⟩, ⟨228, 2, 59⟩, ⟨230, 2, 59⟩, ⟨232, 2, 57⟩, ⟨234, 4, 55⟩, ⟨238, 2, 50⟩, ⟨240, 2, 55⟩, ⟨242, 2, 55⟩, ⟨244, 2, 57⟩, ⟨246, 1, 59⟩, ⟨247, 1, 62⟩, ⟨248, 3, 62⟩, ⟨251, 1, 60⟩, ⟨252, 2, 59⟩, ⟨254, 2, 59⟩, ⟨256, 2, 57⟩, ⟨258, 4, 55⟩, ⟨262, 2, 62⟩, ⟨264, 1, 64⟩, ⟨265, 1, 62⟩, ⟨266, 4, 60⟩, ⟨270, 2, 59⟩, ⟨272, 2, 57⟩, ⟨274, 2, 54⟩, ⟨276, 6, 55⟩, ⟨282, 6, 59⟩]
  b := [⟨36, 2, 43⟩, ⟨38, 2, 45⟩, ⟨40, 2, 48⟩, ⟨42, 6, 50⟩, ⟨48, 2, 43⟩, ⟨50, 2, 48⟩, ⟨52, 2, 45⟩, ⟨54, 4, 43⟩, ⟨58, 2, 50⟩, ⟨60, 2, 43⟩, ⟨62, 2, 47⟩, ⟨64, 2, 50⟩, ⟨66, 1, 43⟩, ⟨67, 1, 45⟩, ⟨68, 2, 47⟩, ⟨70, 2, 47⟩, ⟨72, 4, 40⟩, ⟨76, 2, 45⟩, ⟨78, 2, 43⟩, ⟨80, 2, 45⟩, ⟨82, 2, 48⟩, ⟨84, 2, 43⟩, ⟨86, 2, 47⟩, ⟨88, 2, 50⟩, ⟨90, 1, 43⟩, ⟨91, 1, 47⟩, ⟨92, 2, 48⟩, ⟨94, 2, 38⟩, ⟨96, 2, 43⟩, ⟨98, 2, 47⟩, ⟨100, 2, 38⟩, ⟨102, 1, 50⟩, ⟨103, 1, 52⟩, ⟨104, 2, 48⟩, ⟨106, 2, 38⟩, ⟨108, 2, 43⟩, ⟨110, 2, 48⟩, ⟨112, 2, 40⟩, ⟨114, 2, 48⟩, ⟨116, 2, 45⟩, ⟨118, 2, 50⟩, ⟨120, 2, 43⟩, ⟨122, 2, 40⟩, ⟨124, 2, 45⟩, ⟨126, 4, 43⟩, ⟨130, 2, 50⟩, ⟨132, 2, 43⟩, ⟨134, 2, 47⟩, ⟨136, 2, 50⟩, ⟨138, 4, 43⟩, ⟨142, 2, 50⟩, ⟨144, 2, 43⟩, ⟨146, 2, 52⟩, ⟨148, 2, 50⟩, ⟨150, 2, 43⟩, ⟨152, 2, 40⟩, ⟨154, 2, 47⟩, ⟨156, 2, 47⟩, ⟨158, 2, 43⟩, ⟨160, 2, 50⟩, ⟨162, 4, 43⟩, ⟨166, 2, 52⟩, ⟨168, 4, 52⟩, ⟨172, 2, 47⟩, ⟨174, 2, 52⟩, ⟨176, 2, 45⟩, ⟨178, 2, 48⟩, ⟨180, 4, 48⟩, ⟨184, 2, 47⟩, ⟨186, 2, 52⟩, ⟨188, 2, 43⟩, ⟨190, 2, 48⟩, ⟨192, 4, 48⟩, ⟨196, 2, 38⟩, ⟨198, 2, 43⟩, ⟨200, 2, 45⟩, ⟨202, 2, 38⟩, ⟨204, 2, 48⟩, ⟨206, 2, 52⟩, ⟨208, 2, 45⟩, ⟨210, 2, 38⟩, ⟨212, 2, 40⟩, ⟨214, 2, 38⟩, ⟨216, 2, 40⟩, ⟨218, 2, 48⟩, ⟨220, 2, 38⟩, ⟨222, 2, 43⟩, ⟨224, 4, 50⟩, ⟨228, 2, 43⟩, ⟨230, 2, 40⟩, ⟨232, 2, 50⟩, ⟨234, 4, 43⟩, ⟨238, 2, 47⟩, ⟨240, 4, 40⟩, ⟨244, 2, 45⟩, ⟨246, 2, 43⟩, ⟨248, 4, 50⟩, ⟨252, 2, 43⟩, ⟨254, 2, 40⟩, ⟨256, 2, 50⟩, ⟨258, 4, 43⟩, ⟨262, 2, 38⟩, ⟨264, 2, 48⟩, ⟨266, 2, 48⟩, ⟨268, 2, 48⟩, ⟨270, 6, 50⟩, ⟨276, 4, 43⟩, ⟨280, 2, 48⟩, ⟨282, 6, 43⟩]
}
def fs := timeline voices config.totalTicks
theorem configuration_result : (validConfig config) = true := by decide
#print axioms configuration_result
theorem events_result : (wellFormed voices config.totalTicks) = true := by decide
#print axioms events_result
theorem direct_result : (checkNoDirect fs) = false := by decide
#print axioms direct_result
theorem parallel_result : (checkNoParallel fs) = true := by decide
#print axioms parallel_result
theorem battuta_result : (checkNoBattuta fs) = false := by decide
#print axioms battuta_result
theorem pulse_result : (checkStructural voices config.totalTicks config.pulseStride config.pulseOffset) = false := by decide
#print axioms pulse_result
theorem stagger_result : (checkNoStaggeredPerfects fs) = false := by decide
#print axioms stagger_result
theorem crossing_result : (fs.all noCrossing) = true := by decide
#print axioms crossing_result
theorem ranges_result : (fs.all (voiceRanges config)) = true := by decide
#print axioms ranges_result
theorem scale_result : (fs.all (inScale config)) = false := by decide
#print axioms scale_result
theorem melody_result : (checkMelody voices) = false := by decide
#print axioms melody_result
theorem tritones_result : (checkTritones config fs) = false := by decide
#print axioms tritones_result
theorem independence_result : (hasRhythmicIndependence config voices) = true := by decide
#print axioms independence_result
theorem rejected_result : (certified config voices) = false := by decide
#print axioms rejected_result
end Review
