import os

def compare_to_ground_truth(program_name: str,
                            work_path: str = 'current_program.py',
                            correct_root: str = r"D:\aarush\VS CODE PROJECTS\Auto Code Corrector'\Code-Refactoring-QuixBugs\correct_python_programs") -> bool:
    """
    Return True if the contents of work_path exactly match the
    ground-truth file correct_root/program_name, else False.
    """
    correct_path = os.path.join(correct_root, program_name)
    try:
        with open(work_path, 'r') as f_work, open(correct_path, 'r') as f_corr:
            return f_work.read() == f_corr.read()
    except FileNotFoundError:
        return False
