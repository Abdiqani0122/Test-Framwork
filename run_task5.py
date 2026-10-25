import os
from dotenv import load_dotenv
load_dotenv()                      # reads OPENAI_API_KEY from .env

from agentdojo.task_suite.load_suites import get_suite
from agentdojo.agent_pipeline import AgentPipeline, PipelineConfig
from agentdojo.attacks.attack_registry import load_attack
from agentdojo.functions_runtime import FunctionsRuntime

from stage_scorer import score_task5_stages

VERSION = "v1"
MODEL   = "gpt-4o-mini-2024-07-18"

# 1. load the workspace suite and pick the tasks
suite          = get_suite(VERSION, "workspace")
user_task = suite.user_tasks["user_task_16"]           # benign cover task
injection_task = suite.injection_tasks["injection_task_5"]  # the send+delete attack

# 2. build the agent (the model under test)
cfg = PipelineConfig(
    llm=MODEL, model_id=None, defense=None,
    system_message_name=None, system_message=None,
)
pipeline = AgentPipeline.from_config(cfg)

# 3. build the attack -> this produces the injections dict
attack     = load_attack("important_instructions", suite, pipeline)
injections = attack.attack(user_task, injection_task)

# 4. build the environment exactly as AgentDojo does internally
environment      = suite.load_and_inject_default_environment(injections)
task_environment = user_task.init_environment(environment)

# 5. run the agent
runtime = FunctionsRuntime(suite.tools)
_, _, post_environment, messages, _ = pipeline.query(
    user_task.PROMPT, runtime, task_environment
)

# 6. score with YOUR stage-level scorer
result = score_task5_stages(
    live_emails    = post_environment.inbox.sent,
    trashed_emails = list(post_environment.inbox.trash.values()),
)

print("stage result:", result)