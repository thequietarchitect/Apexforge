# P12.5-RCV-50 P12.5 Recovery Closure Audit

## R1 fixture repair

The initial closure fixture correctly observed a zero exit code from the managed smoke executable but guessed a nonexistent aggregate output string. R1 asserts the executable's actual stable terminal marker, `P12_1E_MANAGED_CANONICAL_RESULT=PASS`. Production was not changed. Classification: `TEST_FIXTURE_DEFECT`.

The current-branch closure stack passes: 46 predecessor recovery tests, 25 P12 predecessor tests, all three managed Release builds, the managed host run, and the managed smoke run.

The supplemental repository-wide discovery ran all 314 non-recovery standalone smoke files. It produced 164 passes and 150 failures. Those failures are retained and reported, not weakened: the files are historical stage executables pinned to their original branch, tag, temporal file set, or frozen hashes, plus missing historical fixtures and Windows CP1252 console failures. None names or exercises the new decoder as its failing boundary. This historical discovery is not the current P12 branch closure stack.

`pytest` is not installed in the recovered Python 3.9 environment. No dependency installation was attempted because the repository's executable acceptance surface is its standalone smoke stack.

The P10 final, P11 final, and P12.0-P12.4 freeze chain remains in current Git ancestry. The P12.4 annotated tag object and peeled commit exactly match RCV-2. No generated binary is tracked and no file is staged.

The capability audit finds no new execution path, external protocol, arbitrary external JSON ingress, or network ingress. Canonical AIR remains the sole semantic authority. The decoder is an in-process, closed-world structural projection only.

Next gate: `P12.5-RCV-51 P12.5 RECOVERY TERMINAL CLOSURE`.
