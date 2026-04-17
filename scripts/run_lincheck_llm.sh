#!/usr/bin/env bash

CPU_COUNT=20
FULL_EVALUATION=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --cpu)
            CPU_COUNT="$2"
            shift 2
            ;;
        --full-evaluation)
            FULL_EVALUATION=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--cpu <number>] [--full-evaluation]"
            echo "  --cpu <number>      Number of CPU cores to use (default: 20)"
            echo "  --full-evaluation   Run full evaluation with all tools and schedulers (default: false)"
            echo "                      When false, only runs fray with scheduler pos"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Always run fray with scheduler pos (basic evaluation)
python3 -m fray_benchmark run fray lincheck --name realworld --scheduler pos --iterations 5 --timeout=3600 --perf-mode --cpu $CPU_COUNT &
python3 -m fray_benchmark run fray lincheck --name realworld --scheduler llm-4 --iterations 5 --timeout=3600 --perf-mode --cpu $CPU_COUNT &
python3 -m fray_benchmark run fray lincheck --name realworld --scheduler random --iterations 5 --timeout=3600 --perf-mode --cpu $CPU_COUNT &
python3 -m fray_benchmark run fray lincheck --name realworld --scheduler llm-8 --iterations 5 --timeout=3600 --perf-mode --cpu $CPU_COUNT &
wait
python3 -m fray_benchmark run fray lincheck --name realworld --scheduler llm-1 --iterations 5 --timeout=3600 --perf-mode --cpu $CPU_COUNT &
python3 -m fray_benchmark run fray lincheck --name realworld --scheduler pct3 --iterations 5 --timeout=3600 --perf-mode --cpu $CPU_COUNT &
python3 -m fray_benchmark run fray lincheck --name realworld --scheduler surw --iterations 5 --timeout=3600 --perf-mode --cpu $CPU_COUNT &
python3 -m fray_benchmark run fray lincheck --name realworld --scheduler llm-2 --iterations 5 --timeout=3600 --perf-mode --cpu $CPU_COUNT &
wait
