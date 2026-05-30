#!/usr/bin/env bash
# Run pytest with optional parallelism and coverage.
# Usage: bash test.sh [OPTIONS] [PYTEST_ARGS...]
#
# Options:
#   --parallel, -p    Run with -n auto (pytest-xdist)
#   --coverage, -c    Enable coverage reporting
#   --ci              Mimic full CI invocation (-n auto + coverage + xml)
#   --quick, -q       Quick mode: no coverage, quiet output
#
# Extra args are passed through to pytest.

set -euo pipefail

PARALLEL=""
COVERAGE=""
CI_MODE=""
QUIET=""
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --parallel|-p) PARALLEL=1; shift ;;
        --coverage|-c) COVERAGE=1; shift ;;
        --ci)          CI_MODE=1; shift ;;
        --quick|-q)    QUIET=1; shift ;;
        *)             EXTRA_ARGS+=("$1"); shift ;;
    esac
done

CMD=(uv run pytest)

if [[ -n "$CI_MODE" ]]; then
    CMD+=(-n auto --cov=culture --cov-report=xml:coverage.xml --cov-report=term -v)
elif [[ -n "$QUIET" ]]; then
    CMD+=(-q)
    [[ -n "$PARALLEL" ]] && CMD+=(-n auto)
else
    [[ -n "$PARALLEL" ]] && CMD+=(-n auto)
    [[ -n "$COVERAGE" ]] && CMD+=(--cov=culture --cov-report=term)
    CMD+=(-v)
fi

CMD+=(${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"})

echo "Running: ${CMD[*]}"
exec "${CMD[@]}"
