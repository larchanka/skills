---
name: test-driven-development
description: Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions "red-green-refactor", or wants integration tests.
metadata:
   version: 1.2.0
---

# Test-Driven Development

TDD is the red → green loop. This skill is the reference that makes that loop produce tests worth keeping: what a good test is, where tests go, the anti-patterns, and the rules of the loop. Every section applies on every cycle — consult them before and during the loop, not after.

When exploring the codebase, read `CONTEXT.md` (if it exists) so test names and interface vocabulary match the project's domain language, and respect ADRs in the area you're touching.

## What a good test is

Tests verify behavior through public interfaces, not implementation details. The test calls the code the way its user does and checks the result that user would see. Code can change entirely; tests shouldn't. A good test reads like a specification — "user can checkout with valid cart" tells you exactly what capability exists — and survives refactors because it doesn't care about internal structure.

**The "Returned Nothing" Litmus Test:** If the test would still pass when every function returned nothing, throw it out.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for mocking guidelines.

## Seams — where tests go

A **seam** is the public boundary you test at: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals.

**Test only at pre-agreed seams.** Before writing any test, write down the seams under test and confirm them with the user. No test is written at an unconfirmed seam. You can't test everything — agreeing the seams up front is how testing effort lands on the critical paths and complex logic instead of every edge case.

Ask: "What's the public interface, and which seams should we test?"

## Anti-patterns

- **Implementation-coupled** — mocks internal collaborators, tests private methods, or verifies through a side channel (querying the database instead of using the interface). The tell: the test breaks when you refactor but behavior hasn't changed.
- **Tautological** — the assertion recomputes the expected value the way the code does (`expect(add(a, b)).toBe(a + b)`, a snapshot derived by hand the same way, a constant asserted equal to itself), so it passes by construction and can never disagree with the code. Expected values must come from an independent source of truth — a known-good literal, a worked example, the spec.
- **Horizontal slicing** — writing all tests first, then all implementation. Bulk tests verify _imagined_ behavior: you test the _shape_ of things rather than user-facing behavior, the tests go insensitive to real changes, and you commit to test structure before understanding the implementation. Work in **vertical slices** instead — one test → one implementation → repeat, each test a **tracer bullet** that responds to what the last cycle taught you.
- **Green-phase accretion (Conditional Spaghetti)** — turning tests green by accumulating ad-hoc booleans, one-off flags, or special-case branches in existing flows without restructuring them. The minimal code written to pass the test is temporary scaffolding; if not cleaned up during refactoring, it hardens into permanent technical debt across slices.

## Laziness Protocol

- **One decision lives in one place.** Keep single sources of truth.
- **Ship the smallest edit that solves the problem.**
- **Subtract before you add.** Take complexity out before you add anything.
- **Delete scaffolding before the next slice.** Once green, evaluate whether the implementation can be reframed with fewer concepts or simpler defaults before moving to the next Red test.
- **Never accept working spaghetti.** A green test proves correctness, but does not excuse architectural degradation or file bloat.

## Fixing Root Causes

- **Reproduce it first.** Write a failing test demonstrating the bug before touching any code.
- **Fix the cause.** Resolve the underlying defect.
- **A guard that only hides the crash is not a fix.** Never slap on defensive null checks or silent try/excepts that mask root cause bugs.

## Rules of the loop

- **Red before green.** Write the failing test before you change the code. See it fail for the exact reason you expect.
- **Make the smallest change that makes it pass.** Don't anticipate future tests or add speculative features.
- **Honest testing.** If an honest test is impractical, do not write a bad one.
- **One slice at a time.** One seam, one test, one minimal implementation per cycle.
- **Refactoring ("Then Make it Right").** Restructuring and quality gating are separated from the Red-Green loop: once green, transition to the `refactoring` skill to pin behavior, clean up duplication, eliminate ad-hoc conditionals, enforce CRAP < 10, eliminate mutants, and find the "code judo" move that makes the implementation feel inevitable in hindsight. Never let a vertical slice push a file past the 1,000-line boundary without decomposing it.