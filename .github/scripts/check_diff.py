import json
import sys
import os
from typing import Dict

LANGCHAIN_DIRS = [
    "libs/core",
    "libs/text-splitters",
    "libs/langchain",
    "libs/community",
    "libs/experimental",
]

if __name__ == "__main__":
    files = sys.argv[1:]

    dirs_to_run: Dict[str, set] = {
        "lint": set(),
        "test": set(),
        "extended-test": set(),
    }
    docs_edited = False

    if len(files) == 300:
        # max diff length is 300 files - there are likely files missing
        raise ValueError("Max diff reached. Please manually run CI on changed libs.")

    for file in files:
        if any(
            file.startswith(dir_)
            for dir_ in (
                ".github/workflows",
                ".github/tools",
                ".github/actions",
                ".github/scripts/check_diff.py",
            )
        ):
            # add all LANGCHAIN_DIRS for infra changes
            dirs_to_run["extended-test"].update(LANGCHAIN_DIRS)
            dirs_to_run["lint"].add(".")

        if any(file.startswith(dir_) for dir_ in LANGCHAIN_DIRS):
            # add that dir and all dirs after in LANGCHAIN_DIRS
            # for extended testing
            found = False
            for dir_ in LANGCHAIN_DIRS:
                if file.startswith(dir_):
                    found = True
                if found:
                    dirs_to_run["extended-test"].add(dir_)
        elif file.startswith("libs/standard-tests"):
            # TODO: update to include all packages that rely on standard-tests (all partner packages)
            # note: won't run on external repo partners
            dirs_to_run["lint"].add("libs/standard-tests")
            dirs_to_run["test"].add("libs/partners/mistralai")
            dirs_to_run["test"].add("libs/partners/openai")
            dirs_to_run["test"].add("libs/partners/anthropic")
            dirs_to_run["test"].add("libs/partners/ai21")
            dirs_to_run["test"].add("libs/partners/fireworks")
            dirs_to_run["test"].add("libs/partners/groq")

        elif file.startswith("libs/cli"):
            # todo: add cli makefile
            pass
        elif file.startswith("libs/partners"):
            partner_dir = file.split("/")[2]
            if os.path.isdir(f"libs/partners/{partner_dir}") and [
                filename
                for filename in os.listdir(f"libs/partners/{partner_dir}")
                if not filename.startswith(".")
            ] != ["README.md"]:
                dirs_to_run["test"].add(f"libs/partners/{partner_dir}")
            # Skip if the directory was deleted or is just a tombstone readme
        elif file.startswith("libs/"):
            raise ValueError(
                f"Unknown lib: {file}. check_diff.py likely needs "
                "an update for this new library!"
            )
        elif any(file.startswith(p) for p in ["docs/", "templates/", "cookbook/"]):
            if file.startswith("docs/"):
                docs_edited = True
            dirs_to_run["lint"].add(".")

    outputs = {
        "dirs-to-lint": list(
            dirs_to_run["lint"] | dirs_to_run["test"] | dirs_to_run["extended-test"]
        ),
        "dirs-to-test": list(dirs_to_run["test"] | dirs_to_run["extended-test"]),
        "dirs-to-extended-test": list(dirs_to_run["extended-test"]),
        "docs-edited": "true" if docs_edited else "",
    }
    for key, value in outputs.items():
        json_output = json.dumps(value)
        print(f"{key}={json_output}")  # noqa: T201
