from stable_baselines3 import PPO
from repair_env import RepairEnv

bugs = ["Code-Refactoring-QuixBugs/python_programs/bitcount.py", ...]  # list all 40

env = RepairEnv(
    buggy_file=bugs[0],
    code_dir="Code-Refactoring-QuixBugs/python_programs",
    test_script="Code-Refactoring-QuixBugs/tester.py",
    llm_api_key='API_KEY'
)

model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    learning_rate=3e-4,
    ent_coef=0.01,
)

model.learn(total_timesteps=10000)

print("training finished")