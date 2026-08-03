# P11.1A Performance Baseline Harness

## Scope

This internal, observational harness measures the existing ApexForge project
pipeline. It does not add or change a public build command, public run command,
build artifact, grammar rule, AIR model, runtime policy, CLI output, version, or
exit code.

The two tracked fixtures are:

- `minimal`: one source and one directive.
- `representative-linked`: three module-aware sources with imported functions
  and one entry directive.

## What is measured

Each warmup or measured iteration performs a fresh end-to-end operation using
the fixed fixture files:

1. `project_load`: manifest discovery, manifest validation, and UTF-8 source
   snapshotting through `load_project`.
2. `validated_project_build`: compilation, module analysis, linking, entry
   resolution, and runtime validation through `build_project`.
3. `internal_execution`: only the existing `ProjectBuild.execute(context)`
   call. The build's existing entry resolution is preserved.
4. `total`: the complete interval from immediately before project loading to
   immediately after internal execution, including execution-context setup and
   small harness coordination overhead between the named phases.

All intervals use the host monotonic performance clock
`time.perf_counter_ns`. Warmup observations are discarded. The default is one
warmup followed by five measured samples per fixture. Each measured phase
reports minimum, median, mean, maximum, and sample count.

The execution context follows the established project smoke-test convention:
initial state comes from `StateSnapshot.from_program_initials`, authority comes
from `AuthorityEngine.from_grants`, and fixture-specific grants are explicit.
The harness does not define a public authority policy and never calls
`RuntimeEngine.execute(entry_directives=None)`.

## What is excluded

The harness does not measure process startup, Python installation or dependency
setup, console rendering, JSON serialization, or writing the optional JSON
file. It does not change compilation, validation, execution, diagnostics, or
exit behavior based on a timing result. There are no performance thresholds or
speed assertions.

The report never records a username, hostname, absolute repository path, home
directory, credential, or token. Environment metadata is limited to Python
version, operating-system family, processor architecture, and logical processor
count.

## Running the baseline

From the repository root in PowerShell:

```powershell
Push-Location apexforge
py -m tooling.performance_baseline --json-output ..\p11_1a_baseline.json
Pop-Location
```

Override sampling when needed:

```powershell
Push-Location apexforge
py -m tooling.performance_baseline --warmups 2 --samples 10
Pop-Location
```

The command prints a concise human report. `--json-output` additionally writes
the stable JSON form with schema identifier
`apexforge.performance-baseline/v1`.

## JSON schema

The top-level object is exactly:

```text
schema: string ("apexforge.performance-baseline/v1")
clock: string ("time.perf_counter_ns")
duration_unit: string ("nanoseconds")
configuration:
  warmups: integer
  measured_samples: integer
environment:
  python_version: string
  operating_system_family: string
  processor_architecture: string
  logical_processor_count: integer or null
benchmarks: array, in fixed fixture order
  fixture: string
  source_count: integer
  durations:
    project_load: statistics
    validated_project_build: statistics
    internal_execution: statistics
    total: statistics
```

Every `statistics` object is exactly:

```text
minimum_ns: integer
median_ns: number
mean_ns: number
maximum_ns: integer
sample_count: integer
```

JSON object keys are sorted, indentation is two spaces, UTF-8 characters are
preserved, and the representation ends with one newline.

## Advisory interpretation and timing variation

Results are advisory observations, not pass/fail evidence. They establish data
that later work may compare only after a separate reviewed contract defines a
valid comparison method.

Timing varies with interpreter version, operating system scheduling, processor
frequency and power management, logical CPU contention, filesystem cache and
storage state, antivirus scanning, thermal conditions, virtualization, and
other host activity. Warmups reduce some cold-start noise but do not eliminate
these sources of variation.
