import os

SCHEDULERS = {
    "pct3": ['--scheduler=pct', '--llm-iset-feedback', '--num-switch-points=3', '--interruptPoints'],
    "pct15": ['--scheduler=pct', '--llm-iset-feedback', '--num-switch-points=15', '--interruptPoints'],
    "pos": ['--scheduler=pos',  '--llm-iset-feedback', '--interruptPoints'],
    "surw": ['--scheduler=surw', '--llm-iset-feedback', '--interruptPoints'],
    "random": ['--scheduler=random', '--llm-iset-feedback', '--interruptPoints'],
    "llm-1" : ['--scheduler=llm-combined-concurr-fuzz', '--llm-iset-feedback', '--llm-max-runs=1', '--interruptPoints', '--llmdir=/home/michael/Documents/software/fray2/fray/llm-stuff/', "--llm-num-traces-in-prompt=10", "--llm-runs-until-llm=200"],
    "llm-2" : ['--scheduler=llm-combined-concurr-fuzz', '--llm-iset-feedback', '--llm-max-runs=2', '--interruptPoints', '--llmdir=/home/michael/Documents/software/fray2/fray/llm-stuff/', "--llm-num-traces-in-prompt=10", "--llm-runs-until-llm=200"],
    "llm-4" : ['--scheduler=llm-combined-concurr-fuzz', '--llm-iset-feedback', '--llm-max-runs=4', '--interruptPoints', '--llmdir=/home/michael/Documents/software/fray2/fray/llm-stuff/', "--llm-num-traces-in-prompt=10", "--llm-runs-until-llm=200"],
    "llm-8" : ['--scheduler=llm-combined-concurr-fuzz', '--llm-iset-feedback', '--llm-max-runs=8', '--interruptPoints', '--llmdir=/home/michael/Documents/software/fray2/fray/llm-stuff/', "--llm-num-traces-in-prompt=10", "--llm-runs-until-llm=200"],
    "llm-8-gpt5" : ['--scheduler=llm-combined-concurr-fuzz', '--llm-iset-feedback', '--llm-max-runs=8', '--interruptPoints', '--llmdir=/home/michael/Documents/software/fray2/fray/llm-stuff/', "--llm-num-traces-in-prompt=10", "--llm-runs-until-llm=200", "--llm-model=gpt-5"],
    "llm-16" : ['--scheduler=llm-combined-concurr-fuzz', '--llm-iset-feedback', '--llm-max-runs=16', '--interruptPoints', '--llmdir=/home/michael/Documents/software/fray2/fray/llm-stuff/', "--llm-num-traces-in-prompt=10", "--llm-runs-until-llm=200"],
}

FRAY_VERSION = "0.5.2-SNAPSHOT"
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)))
PROJECT_PATH = os.path.join(SCRIPT_PATH, "..")
ARTIFACTS_PATH = os.path.join(PROJECT_PATH, "bms")
ASSETS_PATH = os.path.join(SCRIPT_PATH, "assets")
OUTPUT_PATH = os.path.join(PROJECT_PATH, "output")
TOOL_PATH = os.path.join(PROJECT_PATH, "tools")
FRAY_PATH = os.path.join(TOOL_PATH, "fray")
HELPER_PATH = os.path.join(PROJECT_PATH, "helpers")
RR_PATH = os.path.join(TOOL_PATH, "rr")
JPF_PATH = os.path.join(TOOL_PATH, "jpf-core")
PERF_ITER = 5000
PERF_TRIALS = 10
