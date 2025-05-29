import json
import re
import ast
import pickle
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from defect_classes import DefectClass
from strategy_router import STRATEGY_ROUTER, PROMPT_TEMPLATES

class Middleware:
    def __init__(self, llm, fsm, toolset, static_prompt):
        self.llm       = llm
        self.fsm       = fsm
        self._forced_tool = None      
        model_dir = "defect_classifier_model"
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.classifier = AutoModelForSequenceClassification.from_pretrained(model_dir)
        with open("label_encoder.pkl","rb") as f:
            self.label_encoder = pickle.load(f)

        self._strategy_initialized = False

        self.toolset   = toolset
        self.prompt    = {
            'role':      static_prompt['role'],
            'goals':     static_prompt['goals'],
            'guidelines':static_prompt['guidelines'],
            'tools':     static_prompt['tools'],
            'state':     None,     
            'history':   [],       
        }
    def _maybe_inject_strategy(self):
        if self._strategy_initialized:
            return ""  
        tests = self.fsm.state_data.get('bug_info', {}).get('tests', [])
        if not tests:
            return ""
        
        first_test = tests[0]
        line_no    = first_test.line_no
        method_name= first_test.name
        # Extract context around the buggy line
        start = max(1, line_no - 3)
        end   = line_no + 3
        snippet = self.toolset.read_range(
            file_path="current_program.py",
            start_line=start,
            end_line=end
        )
        # Classify via CodeBERT
        tokens = self.tokenizer(snippet, return_tensors="pt", truncation=True, max_length=512)
        logits = self.classifier(**tokens).logits
        pred  = logits.argmax(dim=-1).item()
        defect_label = self.label_encoder.inverse_transform([pred])[0]
        defect = DefectClass(defect_label)
        # Load strategy & template
        self.fsm.state_data['defect_class']  = defect
        self.fsm.state_data['strategy']      = STRATEGY_ROUTER[defect]
        self.fsm.state_data['strategy_idx']  = 0

        template = PROMPT_TEMPLATES[defect]
        method_body = self.toolset.extract_method("current_program.py", method_name)

        filled = template.format(
            method_name=method_name,
            line_no=line_no,
            orig_condition="<original condition>",  
            method_body=method_body
        )

        self._strategy_initialized = True
        return f"Repair strategy template:\n{filled}\n\n"


    def _force_strategy_tool(self, proposed_tool):
        strat = self.fsm.state_data.get('strategy', [])
        idx   = self.fsm.state_data.get('strategy_idx', 0)
        if idx < len(strat):
            next_tool = strat[idx]
            self.fsm.state_data['strategy_idx'] = idx + 1
            return next_tool
        return proposed_tool
    
    def override_next_tool(self, tool_name: str, args: dict = None):
        self._forced_tool = (tool_name, args or {})

    def parse_response(self, llm_output: str) -> tuple[str, dict]:
        clean_output = llm_output.strip()
        if clean_output.startswith("```"):
            clean_output = clean_output.strip("`").strip()
            if clean_output.startswith("json"):
                clean_output = clean_output[4:].strip()
        try:
            payload = json.loads(clean_output)
        except Exception:
            try: 
                payload = ast.literal_eval(clean_output)
            except Exception as e:
                print(f"⚠️ parse_response failed: {e}\nRaw output:\n{llm_output}")
                for t in self.prompt['tools']:
                    if re.search(rf'"?{t}"?', llm_output):
                        return t, {}
                return 'run_tests', {}

        name = payload.get('command', {}).get('name')
        args = payload.get('command', {}).get('args', {}) or {}

        if isinstance(name, str):
            return name, args
        
        return 'run_tests', {}

    def invoke_tool(self, tool_name: str, args: dict) -> str:
        if tool_name == "run_tests":
            args["test_script"]=  self.fsm.test_script
            args["file_path"] = self.fsm.state_data.get("algo_name", "bitcount")
        tool = getattr(self.toolset, tool_name, None)
        if not tool:
            return f"Error: unknown tool '{tool_name}'."
        try:
            result = tool(**args)
            return result
        except Exception as e:
            return f"Exception during {tool_name}: {e}"

    def update_prompt(self, command: str, result: str):
        self.prompt['history'].append((command, result))
        self.prompt['state'] = self.fsm.current_state()
        
        dynamic_parts = [
            f"Current state: {self.prompt['state']}",
            "History of commands and results:"
        ] + [f"- {c}: {r}" for c, r in self.prompt['history'][-5:]]
        self.prompt['dynamic'] = "\n".join(dynamic_parts)


    def run_cycle(self):
        # Build the dynamic prompt, injecting strategy template on first cycle
        dynamic = self.prompt.get('dynamic', '')
        injection = self._maybe_inject_strategy()
        if injection:
            dynamic = injection + dynamic
        # 1. Build prompt text
        full_prompt = "\n\n".join([
            self.prompt['role'],
            self.prompt['goals'],
            self.prompt['guidelines'],
            f"Available tools: {', '.join(self.prompt['tools'])}",
            dynamic
        ])
        # 2. Query LLM
        if self._forced_tool is None:
            llm_output = self.llm.generate(full_prompt)
            print("===== DEBUG LLM OUTPUT =====\n", llm_output, "\n=============================\n")
            tool_name, args = self.parse_response(llm_output)
        else:
            llm_output = "<forced-by-override>"
            tool_name, args = self._forced_tool
            self._forced_tool = None

        tool_name = self._force_strategy_tool(tool_name)
        command_desc = f"{tool_name}({args})"

        print(f"===== DEBUG PARSED =====\n tool_name = {tool_name!r}, args = {args!r}\n========================\n")

        self.fsm.state_data.setdefault('analysis_cycles', 0)
        if tool_name != 'write_fix':
            self.fsm.state_data['analysis_cycles'] += 1
        else:
            self.fsm.state_data['analysis_cycles'] = 0

        if self.fsm.state_data['analysis_cycles'] >= 2:
            fix_source = self.fsm.state_data.get('fix')
            if fix_source:
                tool_name = 'write_fix'
                args = {
                    'file_path': 'current_program.py',
                    'new_source': self.fsm.state_data.get('fix','')
                }
        command_desc = f"{tool_name}({args})"

        if tool_name == "write_fix":
            file_path  = args.get("file_path",
                          self.fsm.state_data.get("work_file", "current_program.py"))
            new_source = args.get("new_source",
                          self.fsm.state_data.get("fix", "")) or ""
            diff = self.toolset.write_fix(
                file_path=file_path,
                new_source=new_source
            ) 
            self.fsm.state_data['last_diff'] = diff
            result = diff
        else:
            result = self.invoke_tool(tool_name, args)
            
        self.update_prompt(command_desc, result)
        self.fsm.transition(tool_name, result)
        return llm_output, command_desc, result

