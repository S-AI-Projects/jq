#!/usr/bin/env python3

"""Verify Bob's generated tests and validate the maintained reference safely."""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

try:
    import tomllib
except ModuleNotFoundError:
    from pip._vendor import tomli as tomllib


ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK_DIR = pathlib.Path(__file__).resolve().parent
EXERCISE_REL = pathlib.Path("exercises/practice/bob")
CANONICAL_REVISION = "4812c213a2647e2034ad5ac78155ce9265cdd171"
CANONICAL_SHA256 = "02b79f535d7613c6faba88cb909462892b101dc799b2df68dd9ffb5ec1d1284d"
CANONICAL_URL = (
    "https://raw.githubusercontent.com/exercism/problem-specifications/"
    f"{CANONICAL_REVISION}/exercises/bob/canonical-data.json"
)


def command_result(
    command: list[str],
    *,
    cwd: pathlib.Path,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> dict[str, object]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(error),
        }
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def flatten_cases(cases: list[dict[str, object]]):
    for case in cases:
        children = case.get("cases")
        if isinstance(children, list):
            yield from flatten_cases(children)
        else:
            yield case


def selected_cases(canonical: dict[str, object], metadata: dict[str, dict]) -> list[dict]:
    replaced = {
        test["reimplements"]
        for test in metadata.values()
        if test.get("include", True) and "reimplements" in test
    }
    selected = []
    for case in flatten_cases(canonical["cases"]):
        case_uuid = case["uuid"]
        if (
            case_uuid in metadata
            and case_uuid not in replaced
            and metadata[case_uuid].get("include", True)
        ):
            selected.append(case)
    return selected


def test_names(test_contents: str) -> list[str]:
    names = []
    for match in re.finditer(r"(?m)^@test (.*?) \{$", test_contents):
        parsed = shlex.split(match.group(1))
        if len(parsed) != 1:
            raise AssertionError(f"Could not parse Bats test name: {match.group(0)}")
        names.append(parsed[0])
    return names


def normalize_timestamp(contents: str) -> str:
    lines = contents.splitlines()
    timestamp_lines = [line for line in lines if line.startswith("# generated on ")]
    if len(timestamp_lines) != 1:
        raise AssertionError(
            f"Expected one generated timestamp line, found {len(timestamp_lines)}"
        )
    normalized = [
        "# generated on <timestamp>" if line.startswith("# generated on ") else line
        for line in lines
    ]
    return "\n".join(normalized) + "\n"


def unified_diff(
    expected: str, actual: str, expected_name: str, actual_name: str
) -> str:
    return "".join(
        difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile=expected_name,
            tofile=actual_name,
        )
    )


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, object] = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_source": {"url": CANONICAL_URL, "revision": CANONICAL_REVISION},
        "commands": [],
        "case_results": [],
        "generation_runs": [],
    }

    def check(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    exercise = ROOT / EXERCISE_REL
    config = json.loads((exercise / ".meta/config.json").read_text())
    solution_rel = pathlib.Path(config["files"]["solution"][0])
    test_rel = pathlib.Path(config["files"]["test"][0])
    example_rel = pathlib.Path(config["files"]["example"][0])
    solution_path = exercise / solution_rel
    original_solution_hash = hashlib.sha256(solution_path.read_bytes()).hexdigest()

    canonical_path = TASK_DIR / "canonical-data.json"
    canonical_bytes = canonical_path.read_bytes()
    canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()
    check(
        canonical_hash == CANONICAL_SHA256,
        f"Canonical input SHA-256 mismatch: {canonical_hash}",
    )
    canonical = json.loads(canonical_bytes)
    metadata = tomllib.loads((exercise / ".meta/tests.toml").read_text())
    cases = selected_cases(canonical, metadata)
    expected_names = [case["description"] for case in cases]
    anchors = {
        "8a2e771d-d6f1-4e3f-b6c6-b41495556e37": "asking a question",
        "a5193c61-4a92-4f68-93e2-f554eb385ec6": "forceful question",
        "e162fead-606f-437a-a166-d051915cea8e": "stating something",
    }
    selected_by_uuid = {case["uuid"]: case["description"] for case in cases}
    check(bool(cases), "No enabled canonical cases were selected")
    check(
        all(
            selected_by_uuid.get(case_uuid) == name
            for case_uuid, name in anchors.items()
        ),
        "One or more named Bob cases are missing or mapped to the wrong canonical UUID",
    )
    evidence["canonical_input"] = {
        "path": str(canonical_path.relative_to(ROOT)),
        "sha256": canonical_hash,
        "case_count": len(cases),
    }
    evidence["expected_case_names"] = expected_names
    evidence["anchor_cases"] = [
        {
            "uuid": case_uuid,
            "name": name,
            "selected": selected_by_uuid.get(case_uuid) == name,
        }
        for case_uuid, name in anchors.items()
    ]

    for tool, command in (
        ("python", [sys.executable, "--version"]),
        ("jq", ["jq", "--version"]),
        ("bats", ["bats", "--version"]),
        (
            "jinja2",
            [
                sys.executable,
                "-c",
                "import jinja2; print(jinja2.__version__)",
            ],
        ),
    ):
        result = subprocess.run(command, text=True, capture_output=True, check=True)
        evidence.setdefault("tool_versions", {})[tool] = (
            result.stdout.strip() or result.stderr.strip()
        )
    evidence["tool_versions"]["toml_parser"] = getattr(
        tomllib, "__version__", "stdlib tomllib"
    )

    baseline = (exercise / test_rel).read_text()
    baseline_normalized = normalize_timestamp(baseline)
    check(
        test_names(baseline) == expected_names,
        "Checked-in Bats case names do not match enabled canonical cases",
    )
    evidence["baseline"] = {
        "path": str((EXERCISE_REL / test_rel).as_posix()),
        "sha256": hashlib.sha256(baseline.encode()).hexdigest(),
        "case_names": test_names(baseline),
    }

    with tempfile.TemporaryDirectory(prefix="r07-t022-") as temp_name:
        temp_root = pathlib.Path(temp_name)
        generation_outputs: list[str] = []
        compatibility = temp_root / "python-compat"
        compatibility.mkdir()
        (compatibility / "sitecustomize.py").write_text(
            "import datetime, sys\n"
            "if not hasattr(datetime, 'UTC'):\n"
            "    datetime.UTC = datetime.timezone.utc\n"
            "try:\n"
            "    import tomllib\n"
            "except ModuleNotFoundError:\n"
            "    from pip._vendor import tomli\n"
            "    tomli.load = lambda fp, parse_float=float: "
            "tomli.loads(fp.read().decode('utf-8'), parse_float=parse_float)\n"
            "    sys.modules['tomllib'] = tomli\n"
        )
        generator_env = os.environ.copy()
        existing_pythonpath = generator_env.get("PYTHONPATH")
        generator_env["PYTHONPATH"] = os.pathsep.join(
            part for part in (str(compatibility), existing_pythonpath) if part
        )

        for index in (1, 2):
            specs_root = temp_root / f"specifications-{index}" / "problem-specifications"
            repo_copy = specs_root / "workspace"
            (specs_root / "exercises/bob").mkdir(parents=True)
            shutil.copyfile(canonical_path, specs_root / "exercises/bob/canonical-data.json")
            shutil.copytree(exercise, repo_copy / EXERCISE_REL)
            (repo_copy / "bin").mkdir()
            shutil.copy2(ROOT / "bin/test-generator", repo_copy / "bin/test-generator")

            generated_test = repo_copy / EXERCISE_REL / test_rel
            generated_test.unlink()
            command = [sys.executable, "bin/test-generator", "--no-pull", "bob"]
            result = command_result(command, cwd=repo_copy, env=generator_env)
            evidence["commands"].append(
                {"purpose": f"generation {index}", **result}
            )
            generated_contents = (
                generated_test.read_text() if generated_test.is_file() else ""
            )
            record = {
                "run": index,
                "returncode": result["returncode"],
                "case_names": test_names(generated_contents) if generated_contents else [],
                "sha256": hashlib.sha256(generated_contents.encode()).hexdigest()
                if generated_contents
                else None,
                "timestamp_normalized_match": False,
            }
            evidence["generation_runs"].append(record)
            check(
                result["returncode"] == 0,
                f"Generation run {index} exited with {result['returncode']}: "
                f"{result['stderr']}",
            )
            check(
                generated_test.is_file(),
                f"Generation run {index} did not create {test_rel}",
            )
            if generated_contents:
                generation_outputs.append(generated_contents)
                check(
                    test_names(generated_contents) == expected_names,
                    f"Generation run {index} selected an unexpected case list",
                )
                normalized_generation = generated_contents
                try:
                    normalized_generation = normalize_timestamp(generated_contents)
                    same_as_baseline = normalized_generation == baseline_normalized
                except AssertionError as error:
                    failures.append(f"Generation run {index}: {error}")
                    same_as_baseline = False
                record["timestamp_normalized_match"] = same_as_baseline
                if not same_as_baseline:
                    record["diff"] = unified_diff(
                        baseline_normalized,
                        normalized_generation,
                        "checked-in test-bob.bats",
                        f"generation-{index} test-bob.bats",
                    )
                check(
                    same_as_baseline,
                    f"Generation run {index} differs from checked-in tests "
                    "beyond the timestamp:\n" + record.get("diff", ""),
                )

        if len(generation_outputs) == 2:
            try:
                same_generations = normalize_timestamp(
                    generation_outputs[0]
                ) == normalize_timestamp(generation_outputs[1])
            except AssertionError as error:
                failures.append(f"Generated output comparison: {error}")
                same_generations = False
            check(same_generations, "The two fresh generations differ")
            evidence["generation_runs_agree"] = same_generations
            if not same_generations:
                try:
                    normalized_first = normalize_timestamp(generation_outputs[0])
                    normalized_second = normalize_timestamp(generation_outputs[1])
                    evidence["generation_diff"] = unified_diff(
                        normalized_first,
                        normalized_second,
                        "generation-1 test-bob.bats",
                        "generation-2 test-bob.bats",
                    )
                except AssertionError as error:
                    evidence["generation_diff"] = str(error)

        validation_root = temp_root / "validation-copy"
        shutil.copytree(exercise, validation_root / EXERCISE_REL)
        validation_repo = validation_root / EXERCISE_REL
        (validation_root / "bin").mkdir()
        shutil.copy2(
            ROOT / "bin/validate_one_exercise",
            validation_root / "bin/validate_one_exercise",
        )
        shutil.copyfile(
            validation_repo / example_rel, validation_repo / solution_rel
        )

        validator_command = [
            "bin/validate_one_exercise",
            EXERCISE_REL.as_posix(),
        ]
        validator = command_result(validator_command, cwd=validation_root)
        evidence["commands"].append({"purpose": "reference validation", **validator})
        validator_stdout = str(validator["stdout"])
        passed_lines = re.findall(r"(?m)^ok \d+(?: .*)?$", validator_stdout)
        failed_lines = re.findall(r"(?m)^not ok \d+.*$", validator_stdout)
        plans = re.findall(r"(?m)^1\.\.(\d+)\s*$", validator_stdout)
        evidence["validator"] = {
            "returncode": validator["returncode"],
            "planned_tests": [int(plan) for plan in plans],
            "passed_count": len(passed_lines),
            "failed_lines": failed_lines,
            "output": validator_stdout,
            "stderr": validator["stderr"],
        }
        check(
            validator["returncode"] == 0,
            f"Reference validation exited with {validator['returncode']}: "
            f"{validator['stderr']}",
        )
        check(bool(plans), "Reference validation produced no TAP test plan")
        check(
            len(passed_lines) > 0,
            "Reference validation executed zero passing tests",
        )
        check(
            len(passed_lines) == len(cases),
            f"Reference validation passed {len(passed_lines)} tests; "
            f"expected {len(cases)}",
        )
        check(
            plans == [str(len(cases))],
            f"Unexpected TAP plan: {plans!r}; expected {len(cases)} tests",
        )
        check(not failed_lines, f"Reference validation had failures: {failed_lines}")

        for case in cases:
            jq_result = command_result(
                ["jq", "-r", "-f", str(solution_rel)],
                cwd=validation_repo,
                input_text=json.dumps(case["input"], separators=(",", ":")),
            )
            actual = str(jq_result["stdout"]).rstrip("\n")
            case_result = {
                "name": case["description"],
                "uuid": case["uuid"],
                "input": case["input"],
                "expected": case["expected"],
                "actual": actual,
                "returncode": jq_result["returncode"],
                "stderr": jq_result["stderr"],
                "passed": jq_result["returncode"] == 0 and actual == case["expected"],
            }
            evidence["case_results"].append(case_result)
            check(
                bool(case_result["passed"]),
                f"Reference result mismatch for {case['description']}: "
                f"expected {case['expected']!r}, got {actual!r}",
            )

    after_solution_hash = hashlib.sha256(solution_path.read_bytes()).hexdigest()
    evidence["learner_solution"] = {
        "path": (EXERCISE_REL / solution_rel).as_posix(),
        "sha256_before": original_solution_hash,
        "sha256_after": after_solution_hash,
        "unchanged": original_solution_hash == after_solution_hash,
    }
    check(
        original_solution_hash == after_solution_hash,
        "The learner solution changed during the check",
    )

    evidence["failures"] = failures
    (TASK_DIR / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(
        f"Reference validation: "
        f"{evidence.get('validator', {}).get('passed_count', 0)} "
        f"of {len(cases)} enabled cases passed."
    )
    if evidence.get("generation_runs_agree"):
        print("Two fresh test generations match after timestamp normalization.")
    print(f"Evidence: {(TASK_DIR / 'evidence.json').relative_to(ROOT)}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
