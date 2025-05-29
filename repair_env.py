import gym
from gym import spaces
import numpy as np
from fsm import RepairAgentFSM
from Middleware import Middleware
from tools import Toolset
from llm_interface import GeminiLLM
import shutil
from tools import Toolset
import os

TEST_DIR=os.path.join('Code-Refactoring-QuixBugs', 'json_testcases')
BUGGY_DIR = os.path.join('Code-Refactoring-QuixBugs', 'python_programs')

tools = Toolset(code_dir=BUGGY_DIR, test_dir=TEST_DIR)

class RepairEnv(gym.Env):
    def __init__(self, buggy_file: str, code_dir: str, test_script: str, llm_api_key: str):
        super().__init__()
        self.tool_names = [t for t in dir(Toolset) if not t.startswith('_')]
        self.n_actions = len(self.tool_names)
        self.obs_dim   = 6 + 2 * self.n_actions
        self.action_space = spaces.Discrete(self.n_actions)
        self.observation_space = spaces.Box(0,1,shape=(self.obs_dim,), dtype=np.float32)

        # Initialize components
        self.llm = GeminiLLM(api_key=llm_api_key)
        self.tools = Toolset(code_dir=code_dir, test_dir=code_dir.replace('python_programs','json_testcases'))
        self.fsm = RepairAgentFSM(self.llm, self.tools, test_script, max_cycles=10)

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
        self.static_prompt = static_prompt
        self.middleware = Middleware(self.llm, self.fsm, self.tools, static_prompt=static_prompt)
        self.buggy_file = buggy_file

    def reset(self):
        shutil.copy(self.buggy_file, 'current_program.py')
        self.fsm = RepairAgentFSM(self.llm, self.tools, self.middleware.fsm.test_script)
        self.middleware = Middleware(self.llm, self.fsm, self.tools,  static_prompt=self.static_prompt )
        return self._get_obs()

    def _get_obs(self):
        states = ['INIT','GATHER_INFO','GENERATE_FIX','VALIDATE_FIX','GOAL_ACCOMPLISHED', 'FAILED']
        state_vec = np.zeros(len(states))
        state_vec[states.index(self.fsm.current_state())] = 1
        last_two = self.middleware.prompt.get('history',[])[-2:]
        act_vecs = []
        for _,_ in enumerate(range(2)):
            if _ < len(last_two):
                name = last_two[_][0].split('(')[0]
                idx = self.tool_names.index(name)
                vec = np.zeros(self.n_actions); vec[idx]=1
            else:
                vec = np.zeros(self.n_actions)
            act_vecs.append(vec)
        obs = np.concatenate([state_vec] + act_vecs)
        assert obs.shape == (self.obs_dim,)
        return obs

    def step(self, action: int):
        tool = self.tool_names[action]
        self.middleware.override_next_tool(tool)
        llm_out, cmd, result = self.middleware.run_cycle()
        done = self.fsm.is_done()
        if done:
            if self.fsm.current_state()=='GOAL_ACCOMPLISHED':
                reward = 1.0
            else:
                reward = -1.0
        else:
            reward = 0.0
        obs = self._get_obs()
        return obs, reward, done, {}

    def render(self, mode='human'):
        pass
