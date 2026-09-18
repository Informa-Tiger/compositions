import Counterpoint

open Counterpoint
namespace RuleFixtures

-- Tests are propositions discharged by Lean's kernel, not native evaluation.
def cMajor : Config := {
  totalTicks := 4, ticksPerQuarter := 2, tonicPc := 0, tonicThird := 4,
  allowedPcs := [0, 2, 4, 5, 7, 9, 11],
  ranges := [(1, 127), (1, 127), (1, 127), (1, 127)],
  maxLeaps := [7, 7, 7, 12], pulseStride := 2, pulseOffset := 0,
  tritoneMaxWait := 2, requireIndependence := false, minIndependentChanges := 1
}

def cMinor : Config := { cMajor with
  tonicThird := 3, allowedPcs := [0, 2, 3, 5, 7, 8, 11] }
def dMajor : Config := { cMajor with
  tonicPc := 2, allowedPcs := [1, 2, 4, 6, 7, 9, 11] }
def bMajor : Config := { cMajor with
  tonicPc := 11, allowedPcs := [1, 3, 4, 6, 8, 10, 11] }

theorem validCMajor : validConfig cMajor = true := by decide
theorem validD : validConfig dMajor = true := by decide
theorem validMinor : validConfig cMinor = true := by decide
theorem badTotal : validConfig { cMajor with totalTicks := 0 } = false := by decide
theorem badResolution : validConfig { cMajor with ticksPerQuarter := 0 } = false := by decide
theorem badTonic : validConfig { cMajor with tonicPc := 12 } = false := by decide
theorem badThird : validConfig { cMajor with tonicThird := 5 } = false := by decide
theorem emptyScale : validConfig { cMajor with allowedPcs := [] } = false := by decide
theorem badPC : validConfig { cMajor with allowedPcs := [0, 12] } = false := by decide
theorem badRangeCount : validConfig { cMajor with ranges := [(1, 127)] } = false := by decide
theorem reversedRange : validConfig { cMajor with
    ranges := [(70, 60), (1, 127), (1, 127), (1, 127)] } = false := by decide
theorem zeroLeap : validConfig { cMajor with maxLeaps := [7, 7, 7, 0] } = false := by decide
theorem badLeapCount : validConfig { cMajor with maxLeaps := [7] } = false := by decide
theorem zeroPulse : validConfig { cMajor with pulseStride := 0 } = false := by decide
theorem badOffset : validConfig { cMajor with pulseOffset := 2 } = false := by decide
theorem zeroWait : validConfig { cMajor with tritoneMaxWait := 0 } = false := by decide
theorem zeroIndependence : validConfig { cMajor with minIndependentChanges := 0 } = false := by decide

-- Similar-motion arrivals are forbidden even when the upper voice steps,
-- and even if the previous interval was imperfect ("hidden/direct").
theorem directOctave : directPerfect 71 43 72 48 = true := by decide
theorem directFifth : directPerfect 72 48 74 55 = true := by decide
theorem obliqueOctave : directPerfect 72 43 72 48 = false := by decide
theorem contraryFifth : directPerfect 72 48 74 43 = false := by decide
theorem parallelFifths : parallelPerfect 67 60 69 62 = true := by decide
theorem parallelOctaves : parallelPerfect 72 60 74 62 = true := by decide
theorem inwardOctave : battuta 76 60 74 62 = true := by decide

def innerDirectStart : Frame := ⟨some 79, some 71, some 62, some 43⟩
def innerDirectEnd : Frame := ⟨some 79, some 72, some 62, some 48⟩
theorem innerDirectDetected : allPairsSafe directPerfect innerDirectStart innerDirectEnd = false := by decide
theorem restingEndpointSafe : absentOrSafe directPerfect
    (some 71) none (some 72) (some 48) = true := by decide
theorem staggeredDirectUpperFirst : alternatingStagger
    (some 71, some 43) (some 72, some 43) (some 72, some 48) = true := by decide
theorem staggeredDirectLowerFirst : alternatingStagger
    (some 71, some 43) (some 71, some 48) (some 72, some 48) = true := by decide
theorem staggeredContrarySafe : alternatingStagger
    (some 71, some 43) (some 72, some 43) (some 72, some 41) = false := by decide

-- A slower, declared sample catches a direct motion hidden by displaced
-- attacks; the adjacent-tick check alone accepts these oblique transitions.
def pulseHidden : Voices := ⟨[⟨0, 1, 71⟩, ⟨1, 3, 72⟩], [], [],
  [⟨0, 2, 43⟩, ⟨2, 2, 48⟩]⟩
theorem adjacentAloneMissesStagger : checkNoDirect (timeline pulseHidden 4) = true := by decide
theorem pulseCatchesStagger : checkStructural pulseHidden 4 2 0 = false := by decide
theorem projectionCatchesStagger : checkNoStaggeredPerfects (timeline pulseHidden 4) = false := by decide

-- A rest is an absence, breaks melodic continuity, and does not turn a
-- reentry into an independently changing contiguous note.
theorem gapIsSilent : soundingAt [⟨0, 1, 60⟩, ⟨2, 2, 66⟩] 1 = none := by decide
theorem contiguousTritoneFails : checkMelodicVoice [⟨0, 1, 60⟩, ⟨1, 1, 66⟩] = false := by decide
theorem restBreaksTritone : checkMelodicVoice [⟨0, 1, 60⟩, ⟨2, 1, 66⟩] = true := by decide
theorem zeroDurationFails : wellFormedVoice [⟨0, 0, 60⟩] 4 = false := by decide
theorem overlapFails : wellFormedVoice [⟨0, 3, 60⟩, ⟨2, 2, 62⟩] 4 = false := by decide
theorem outOfBoundsFails : wellFormedVoice [⟨0, 5, 60⟩] 4 = false := by decide
theorem emptyVoiceFails : wellFormedVoice [] 4 = false := by decide
theorem pitchZeroFails : wellFormedVoice [⟨0, 1, 0⟩] 4 = false := by decide

def vC : Frame := ⟨some 65, some 62, some 55, some 47⟩
def iC : Frame := ⟨some 64, some 60, some 55, some 48⟩
def iCMinor : Frame := ⟨some 63, some 60, some 55, some 48⟩
def vD : Frame := ⟨some 67, some 64, some 57, some 49⟩
def iD : Frame := ⟨some 66, some 62, some 57, some 50⟩
def vB : Frame := ⟨some 64, some 61, some 54, some 46⟩
def iB : Frame := ⟨some 63, some 59, some 54, some 47⟩

theorem cCadence : resolvesV65 cMajor vC iC = true := by decide
theorem dTransposition : resolvesV65 dMajor vD iD = true := by decide
theorem wrapAtTwelve : resolvesV65 bMajor vB iB = true := by decide
theorem minorCadence : resolvesV65 cMinor vC iCMinor = true := by decide
theorem wrongMinorThird : resolvesV65 cMinor vC iC = false := by decide
theorem wrongKeyCadence : resolvesV65 dMajor vC iC = false := by decide
theorem exactWaitAllowed : checkTritones cMajor [vC, vC, iC] = true := by decide
theorem lateResolutionFails : checkTritones cMajor [vC, vC, vC, iC] = false := by decide
theorem terminalTritoneFails : checkTritones cMajor [vC] = false := by decide
theorem earlySeventhFails : checkTritones cMajor
    [vC, ⟨some 64, some 62, some 55, some 47⟩, iC] = false := by decide
theorem criticalRestFails : checkTritones cMajor
    [vC, ⟨none, some 62, some 55, some 47⟩, iC] = false := by decide
theorem criticalRevoicingFails : checkTritones cMajor
    [vC, ⟨some 77, some 62, some 55, some 47⟩, iC] = false := by decide
theorem wrongInversionFails : checkTritones cMajor
    [⟨some 65, some 62, some 59, some 43⟩, iC] = false := by decide

-- Independence measures pitch-changing contiguous attacks, not the raw
-- number of events. It is strict interior overlap with another held note.
theorem independentChange : independentChangeCount
    [⟨0, 1, 60⟩, ⟨1, 3, 62⟩] [⟨0, 4, 48⟩] 4 = 1 := by decide
theorem rearticulationNotIndependence : independentChangeCount
    [⟨0, 1, 60⟩, ⟨1, 3, 60⟩] [⟨0, 4, 48⟩] 4 = 0 := by decide
theorem reentryNotIndependence : independentChangeCount
    [⟨0, 1, 60⟩, ⟨2, 2, 62⟩] [⟨0, 4, 48⟩] 4 = 0 := by decide
theorem sharedOnsetNotIndependence : independentChangeCount
    [⟨0, 2, 60⟩, ⟨2, 2, 62⟩] [⟨0, 2, 48⟩, ⟨2, 2, 50⟩] 4 = 0 := by decide

def rhythmExample : Voices := ⟨[⟨0, 1, 60⟩, ⟨1, 3, 62⟩],
  [⟨0, 2, 55⟩, ⟨2, 2, 57⟩], [⟨0, 3, 48⟩, ⟨3, 1, 50⟩],
  [⟨0, 1, 36⟩, ⟨1, 3, 38⟩]⟩
theorem independentRhythmAccepted : hasRhythmicIndependence cMajor rhythmExample = true := by decide
theorem thresholdHonored : hasRhythmicIndependence
    { cMajor with minIndependentChanges := 2 } rhythmExample = false := by decide

-- End-to-end aggregate acceptance cannot bypass structural validation.
def staticC : Voices := ⟨[⟨0, 4, 72⟩], [⟨0, 4, 67⟩], [⟨0, 4, 64⟩], [⟨0, 4, 48⟩]⟩
def cadenceC : Voices := ⟨[⟨0, 2, 74⟩, ⟨2, 2, 76⟩],
  [⟨0, 2, 65⟩, ⟨2, 2, 64⟩], [⟨0, 4, 55⟩], [⟨0, 2, 47⟩, ⟨2, 2, 48⟩]⟩
theorem staticAccepted : certified cMajor staticC = true := by decide
theorem cadenceAccepted : certified cMajor cadenceC = true := by decide
theorem requireIndependentRejectsHomophony : certified
    { cMajor with requireIndependence := true } staticC = false := by decide
theorem cannotBypassConfig : certified { cMajor with ranges := [] } staticC = false := by decide
theorem cannotBypassVoice : certified cMajor { staticC with t := [] } = false := by decide

theorem forbiddenScaleNote : certified
    { cMajor with allowedPcs := [0, 7] } staticC = false := by decide
theorem outOfRange : certified { cMajor with
    ranges := [(73, 84), (1, 127), (1, 127), (1, 127)] } staticC = false := by decide

#print axioms cadenceAccepted
#print axioms dTransposition
#print axioms lateResolutionFails
#print axioms requireIndependentRejectsHomophony
end RuleFixtures
