import os
import ast
import re
import subprocess
import logging
import difflib

logging.basicConfig(level=logging.INFO)

class Toolset:
    def __init__(self, code_dir: str, test_dir: str):
        self.code_dir = code_dir
        self.test_dir = test_dir


    def read_range(self, file_path: str, start_line: int, end_line: int) -> str:
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()
            return "".join(lines[start_line - 1:end_line])
        except Exception as e:
            return f"Error in read_range: {e}"

    def get_classes_and_methods(self, file_path: str) -> dict:
        try:
            with open(file_path, "r") as f:
                source = f.read()
            tree = ast.parse(source)
            classes, functions = [], []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
            return {"classes": classes, "methods": functions}
        except Exception as e:
            return {"error": f"get_classes_and_methods: {e}"}

    def extract_method(self, file_path: str, method_name: str) -> str:
        try:
            with open(file_path, "r") as f:
                source = f.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == method_name:
                    return ast.unparse(node)
            return f"Method '{method_name}' not found."
        except Exception as e:
            return f"Error in extract_method: {e}"

    def extract_tests(self, test_output: str) -> list:
        failed_tests = []
        for line in test_output.splitlines():
            if "FAILED" in line or "AssertionError" in line:
                match = re.search(r"test_\w+", line)
                if match:
                    failed_tests.append(match.group(0))
        return list(set(failed_tests))

    def search_code_base(self, keyword: str, code_dir: str = None) -> list:
        root_dir = code_dir or self.code_dir
        matches = []
        for root, _, files in os.walk(root_dir):
            for name in files:
                if name.endswith('.py'):
                    path = os.path.join(root, name)
                    try:
                        with open(path, 'r') as f:
                            for idx, line in enumerate(f.readlines()):
                                if keyword in line:
                                    matches.append((path, idx + 1, line.strip()))
                    except Exception as e:
                        matches.append((path, None, f"search_error: {e}"))
        return matches

    def find_similar_api_calls(self, method_name: str) -> list:
        return self.search_code_base(method_name)

    def generate_method_body(self, prompt: str, llm) -> str:
        return llm.generate(prompt)


    def run_tests(self, test_script: str, file_path: str) -> str:
        try:
            result = subprocess.run(
                ['python', test_script,file_path],cwd='Code-Refactoring-QuixBugs', capture_output=True, text=True, timeout=30
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return "Test execution timed out."
        except Exception as e:
            return f"Error in run_tests: {e}"

    def run_fault_localization(self, test_output: str) -> list:
        return self.extract_tests(test_output)

    def write_fix(self,file_path: str, new_source: str) -> str:
        """
        Overwrite file_path with new_source, returning a unified diff.
        """
        import difflib
        with open(file_path, 'r') as f:
            old = f.read().splitlines(keepends=True)
        new = new_source.splitlines(keepends=True)
        diff = ''.join(difflib.unified_diff(
            old, new,
            fromfile=f"{file_path} (original)",
            tofile=f"{file_path} (patched)",
            lineterm=''
        ))
        if diff:
            with open(file_path, 'w') as f:
                f.write(new_source)
            return diff
        return "No changes made."

    def express_hypothesis(self, hypothesis: str, state: dict) -> str:
        state['hypothesis'] = hypothesis
        return "Hypothesis expressed"

    def discard_hypothesis(self, state: dict) -> str:
        state['hypothesis'] = None
        return "Hypothesis discarded"

    def collect_more_information(self, state: dict) -> str:
        state['status'] = 'collecting_information'
        return "Collecting more information"

    def goal_accomplished(self, state: dict) -> str:
        state['status'] = 'goal_accomplished'
        return "Goal accomplished"
