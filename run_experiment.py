import csv, sys, datetime
from dotenv import load_dotenv
load_dotenv()

from agentdojo.task_suite.load_suites import get_suite
from agentdojo.agent_pipeline import AgentPipeline, PipelineConfig
from agentdojo.attacks.attack_registry import load_attack
from agentdojo.functions_runtime import FunctionsRuntime

from stage_scorer import score_task5_stages

VERSION   = "v1"
MODEL     = "gpt-4o-mini-2024-07-18"
N         = int(sys.argv[1]) if len(sys.argv) > 1 else 20   # uv run run_experiment.py 20
USER_TASK = "user_task_16"

# --- build the fixed pieces once ---
suite          = get_suite(VERSION, "workspace")
user_task      = suite.user_tasks[USER_TASK]
injection_task = suite.injection_tasks["injection_task_5"]

cfg = PipelineConfig(llm=MODEL, model_id=None, defense=None,
                     system_message_name=None, system_message=None)
pipeline = AgentPipeline.from_config(cfg)

attack     = load_attack("important_instructions", suite, pipeline)
injections = attack.attack(user_task, injection_task)

def run_once():
    # fresh environment every run (the agent mutates it)
    environment      = suite.load_and_inject_default_environment(injections)
    task_environment = user_task.init_environment(environment)
    runtime = FunctionsRuntime(suite.tools)
    _, _, post_env, _, _ = pipeline.query(user_task.PROMPT, runtime, task_environment)
    return score_task5_stages(
        live_emails    = post_env.inbox.sent,
        trashed_emails = list(post_env.inbox.trash.values()),
    )

# --- run N times, tally, save ---
tally = {"stage1_sent": 0, "stage2_deleted": 0, "chain_success": 0}
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
csv_path = f"results_{MODEL}_{USER_TASK}_{stamp}.csv"

with open(csv_path, "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["run", "stage1_sent", "stage2_deleted", "chain_success"])
    for i in range(1, N + 1):
        r = run_once()
        for k in tally:
            tally[k] += int(r[k])
        writer.writerow([i, r["stage1_sent"], r["stage2_deleted"], r["chain_success"]])
        print(f"run {i:>3}: {r}")

print("\n=== summary over", N, "runs ===")
for k, v in tally.items():
    print(f"{k:14s}: {v}/{N}  ({v/N:.0%})")
print("saved:", csv_path)