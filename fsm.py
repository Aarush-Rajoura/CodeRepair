class RepairAgentFSM:
    def __init__(self, llm, toolset, test_script, max_cycles=10):
        self.llm = llm
        self.toolset = toolset
        self.test_script = test_script
        self.max_cycles = max_cycles
        self.cycle_count = 0
        self.state = 'INIT'
        self.state_data = {
            'hypothesis': None,
            'bug_info': {},
            'fix': None,
            'attempts': 0,
            'max_attempts': 3,
        }

    def current_state(self):
        return self.state

    def is_done(self):
        return self.state in ['GOAL_ACCOMPLISHED', 'FAILED']

    def transition(self, last_command: str, last_result: str):
        """
        Update FSM state based on the last result of a tool invocation.
        """
        if self.state == 'INIT':
            initial_fails = self.toolset.extract_tests(last_result)
            self.state_data['initial_failures'] = len(initial_fails)
            self.state_data['bug_info']['initial_tests'] = initial_fails
            self.state = 'GATHER_INFO'

        if self.state == 'GATHER_INFO':
            failing = self.toolset.extract_tests(last_result)
            self.state_data['bug_info']['tests'] = failing
            self.state = 'GENERATE_FIX'

        elif self.state == 'GENERATE_FIX':
            new_source = last_result
            self.state_data['fix'] = new_source
            diff = self.toolset.write_fix('current_program.py', new_source)
            self.state_data['last_diff'] = diff
            self.state = 'VALIDATE_FIX'

        elif self.state == 'VALIDATE_FIX':
            failing_after = self.toolset.extract_tests(last_result)
            initial = self.state_data.get('initial_failures', 0)
            diff = self.state_data.get('last_diff', '')
            if initial > 0 and not failing_after and diff and diff != 'No changes made.':
                self.state = 'GOAL_ACCOMPLISHED'
                self.toolset.goal_accomplished(self.state_data)
            else:
                self.state_data['attempts'] += 1
                if self.state_data['attempts'] >= self.state_data['max_attempts']:
                    self.state = 'FAILED'
                else:
                    self.toolset.discard_hypothesis(self.state_data)
                    self.state = 'GATHER_INFO'

    def run(self, middleware):
        while not self.is_done() and self.cycle_count < self.max_cycles:
            self.cycle_count += 1
            middleware.run_cycle()

        return self.state
