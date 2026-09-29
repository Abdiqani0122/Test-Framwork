import inspect_evals.agentdojo as adj
import os

folder = os.path.dirname(adj.__file__)

for sub in ["task_suites", "data"]:
    path = os.path.join(folder, sub)
    print(f"=== {sub} ===")
    for root, dirs, files in os.walk(path):
        # show the folder tree, but keep it shallow
        depth = root.replace(path, "").count(os.sep)
        if depth > 2:
            continue
        indent = "  " * depth
        print(f"{indent}{os.path.basename(root)}/")
        for f in sorted(files):
            print(f"{indent}  {f}")
    print()