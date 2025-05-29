import os
import shutil
import logging
from llm_interface import GeminiLLM
from tools import Toolset
from fsm import RepairAgentFSM
from Middleware import Middleware
from utils import compare_to_ground_truth

TEST_DIR=os.path.join('Code-Refactoring-QuixBugs', 'json_testcases')
BUGGY_DIR = os.path.join('Code-Refactoring-QuixBugs', 'python_programs')
TEST_SCRIPT = os.path.join('Code-Refactoring-QuixBugs', 'tester.py')
WORK_FILE = 'current_program.py'
GEMINI_API_KEY = "API_KEY"
MAX_CYCLES = 10

FIXED_DIR = 'fixed_code'
os.makedirs(FIXED_DIR, exist_ok=True)

code_dir    = os.path.join('Code-Refactoring-QuixBugs', 'python_programs')

tools   = Toolset(code_dir=code_dir, test_dir='.')   

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def evaluate_all():
    results = {}
    files = ['bitcount.py']
    total = len(files)

    for fname in sorted(files):
        logger.info(f"Evaluating {fname}...")
        src_path = os.path.join(BUGGY_DIR, fname)
        shutil.copy(src_path, WORK_FILE)

        # Initialize components
        llm = GeminiLLM(api_key=GEMINI_API_KEY)
        tools = Toolset(code_dir=BUGGY_DIR, test_dir=TEST_DIR)
        fsm = RepairAgentFSM(llm=llm,
                              toolset=tools,
                              test_script=TEST_SCRIPT,
                              max_cycles=MAX_CYCLES)
        
        static_prompt = {
            'role': "You are an expert Python bug fixer agent.",
            'goals': "Locate and fix a single-line defect in the file `current_program.py` using the available tools.",
            'guidelines': (
                "At each step, pick exactly one tool and return a JSON object with:\n"
                "  • `thoughts`: why you chose this tool and what you expect.\n"
                "  • `command`: { `name`: TOOL_NAME, `args`: { ... } }\n\n"

                "TOOLS AND USAGE:\n"
                "1) read_range(file_path: str, start_line: int, end_line: int) → str\n"
                "   • Returns the lines from `start_line` to `end_line` in the file.\n"
                "   • Use this to inspect specific code snippets.\n"
                "   • Example args: {\"file_path\": \"current_program.py\", \"start_line\": 5, \"end_line\": 15}\n\n"

                "2) get_classes_and_methods(file_path: str) → dict\n"
                "   • Returns all class and function names in the file.\n"
                "   • Useful to discover available methods or entry points.\n"
                "   • Example args: {\"file_path\": \"current_program.py\"}\n\n"

                "3) extract_method(file_path: str, method_name: str) → str\n"
                "   • Returns the full source of `method_name`.\n"
                "   • Use when you want the body of a particular function.\n"
                "   • Example args: {\"file_path\": \"current_program.py\", \"method_name\": \"binary_search\"}\n\n"

                "4) extract_tests(test_output: str) → list\n"
                "   • Parses test harness output and returns failing test names.\n"
                "   • Use after `run_tests` to know which cases failed.\n"
                "   • Example args: {\"test_output\": \"(raw output)\"}\n\n"

                "5) search_code_base(keyword: str, code_dir: str) → list\n"
                "   • Finds lines containing `keyword` across all .py files in `code_dir`.\n"
                "   • Use to find related usage or similar logic.\n"
                "   • Example args: {\"keyword\": \"range(\", \"code_dir\": \"python_programs\"}\n\n"

                "6) find_similar_api_calls(method_name: str) → list\n"
                "   • Shortcut for `search_code_base(method_name, code_dir)`.\n\n"

                "7) generate_method_body(prompt: str, llm: object) → str\n"
                "   • Ask the LLM to draft a new method or full source based on your prompt.\n"
                "   • Use to propose the fixed code before writing it.\n"
                "   • Example args: {\"prompt\": \"Fix the off-by-one in this loop...\", \"llm\": LLM_OBJECT}\n\n"

                "8) run_tests(test_script: str, file_path: str) → str\n"
                "   • Runs `tester.py current_program.py` and returns combined stdout/stderr.\n"
                "   • Use only `tester.py` and `current_program.py` for test_script and file_path respectively. These are injected automatically.\n"

                "9) run_fault_localization(test_output: str) → list\n"
                "   • Identical to `extract_tests`, returns failing test names.\n\n"

                "10) write_fix(file_path: str, new_source: str) → str\n"
                "   • Overwrites `file_path` with `new_source` and returns a unified diff.\n"
                "   • Use this when you have the complete fixed file.\n"
                "   • Example args: {\"file_path\": \"current_program.py\", \"new_source\": \"<full file>\"}\n\n"

                "11) express_hypothesis(hypothesis: str, state: dict) → str\n"
                "   • Record your current bug hypothesis into the agent’s state.\n\n"

                "12) discard_hypothesis(state: dict) → str\n"
                "   • Clear the last hypothesis when it’s invalidated.\n\n"

                "13) collect_more_information(state: dict) → str\n"
                "   • Signal to return to gathering info (e.g., after a failed fix).\n\n"

                "**Important:** After doing *any* analysis (run_tests, extract_method, etc), "
                "you must *then* call `write_fix` exactly once, with the full corrected source. "
                "Do *not* call run_tests again until after applying a patch."

                "Always include **only** the JSON in your response—no additional text."
            ),
            'tools': [t for t in dir(tools) if not t.startswith('_')]
        }

        mw = Middleware(llm=llm, fsm=fsm, toolset=tools, static_prompt=static_prompt)

        # Run the repair FSM
        fsm.state_data["algo_name"] = fname.replace(".py", "")
        final_state = fsm.run(mw)

        diff = fsm.state_data.get('last_diff', None)
        results[fname] = {
            'fixed': final_state == 'GOAL_ACCOMPLISHED',
            'attempts': fsm.state_data.get('attempts', fsm.cycle_count),
            'diff': diff,
            'exact_match': compare_to_ground_truth(fname, WORK_FILE),
        }
    
        if results[fname]['fixed']:
            dest = os.path.join(FIXED_DIR, fname)
            shutil.copy(WORK_FILE, dest)
            logger.info(f"Saved patched code to {dest}")

        if diff and diff != "No changes made.":
            print(f"\n📄 Patch for {fname}:\n{diff}")

        attempts = fsm.state_data.get('attempts', fsm.cycle_count)
        success = (final_state == 'GOAL_ACCOMPLISHED')
        logger.info(f"Result for {fname}: fixed={success}, attempts={attempts}\n")
        
  

    # Summarize
    fixed_count = sum(1 for r in results.values() if r['fixed'])
    logger.info("=== Evaluation Summary ===")
    logger.info(f"Total programs: {total}")
    logger.info(f"Fixed: {fixed_count}/{total} ({fixed_count/total:.1%})")

    print("\nProgram\tFixed\tAttempts\tExactMatch")
    for fname, info in results.items():
        print(f"{fname}\t{info['fixed']}\t{info['attempts']}\t{info.get('matched_ground_truth', False)}")

if __name__ == '__main__':
    evaluate_all()
