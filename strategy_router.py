from defect_classes import DefectClass

STRATEGY_ROUTER = {
    DefectClass.MISSING_OR_ADDED_1: [
        "extract_method", "generate_method_body", "write_fix"
    ],
    DefectClass.INCORRECT_COMPARISON_OPERATOR: [
        "extract_method", "generate_method_body", "write_fix"
    ],
    DefectClass.INCORRECT_ARRAY_SLICE: [
        "extract_method", "generate_method_body", "write_fix"
    ],
    DefectClass.MISSING_CONDITION: [
        "extract_method", "generate_method_body", "write_fix"
    ],
    DefectClass.MISSING_BASE_CASE: [
        "extract_method", "generate_method_body", "write_fix"
    ],
    DefectClass.INCORRECT_DATA_STRUCTURE_CONSTANT: [
        "extract_method", "generate_method_body", "write_fix"
    ],
    DefectClass.MISSING_FUNCTION_CALL: [
        "extract_method", "generate_method_body", "write_fix"
    ],
    DefectClass.INCORRECT_METHOD_CALLED: [
        "extract_method", "generate_method_body", "write_fix"
    ],
    DefectClass.INCORRECT_FIELD_DEREFERENCE: [
        "extract_method", "generate_method_body", "write_fix"
    ],
    DefectClass.OFF_BY_ONE: [
        "extract_method", "generate_method_body", "write_fix"
    ],
    DefectClass.INCORRECT_ASSIGNMENT_OPERATOR: [
        "extract_method", "generate_method_body", "write_fix"
    ],
    DefectClass.INCORRECT_OPERATOR: [
        "extract_method", "generate_method_body", "write_fix"
    ]
}

PROMPT_TEMPLATES = {
    DefectClass.MISSING_OR_ADDED_1: (
        "The method `{method_name}` has a +1 offset bug in iteration or condition.\n"
        "Extracted code:\n```python\n{method_body}\n```\n\n"
        "Fix the off-by-one issue and return the complete fixed source."
    ),
    DefectClass.INCORRECT_COMPARISON_OPERATOR: (
        "`{method_name}` uses an incorrect comparison operator (e.g., `==` vs `!=`).\n"
        "Here is the method:\n```python\n{method_body}\n```\n\n"
        "Correct the comparison and return the full updated file."
    ),
    DefectClass.INCORRECT_ARRAY_SLICE: (
        "`{method_name}` seems to access an array with an incorrect slice.\n"
        "Inspect and fix the slicing logic:\n```python\n{method_body}\n```\n"
        "Return the full corrected file."
    ),
    DefectClass.MISSING_CONDITION: (
        "`{method_name}` appears to lack a required conditional (e.g., if-check).\n"
        "Code:\n```python\n{method_body}\n```\n"
        "Please include the missing condition and return the full source."
    ),
    DefectClass.MISSING_BASE_CASE: (
        "`{method_name}` lacks a proper base case for recursion.\n"
        "Code:\n```python\n{method_body}\n```\n"
        "Add the base case and return the fixed code."
    ),
    DefectClass.INCORRECT_DATA_STRUCTURE_CONSTANT: (
        "`{method_name}` uses a wrong constant tied to a data structure (e.g., wrong list size).\n"
        "Fix this and return the full corrected file:\n```python\n{method_body}\n```"
    ),
    DefectClass.MISSING_FUNCTION_CALL: (
        "`{method_name}` is missing a necessary function call.\n"
        "Detected code:\n```python\n{method_body}\n```\n"
        "Add the function call and return the complete source."
    ),
    DefectClass.INCORRECT_METHOD_CALLED: (
        "`{method_name}` uses the wrong method (e.g., `pop` vs `remove`).\n"
        "Correct this in:\n```python\n{method_body}\n```\n"
        "Return the full corrected code."
    ),
    DefectClass.INCORRECT_FIELD_DEREFERENCE: (
        "`{method_name}` tries to access a field incorrectly.\n"
        "Review this method:\n```python\n{method_body}\n```\n"
        "Fix the field dereference and provide the full source."
    ),
    DefectClass.OFF_BY_ONE: (
        "`{method_name}` has an off-by-one issue.\n"
        "Please correct it:\n```python\n{method_body}\n```\n"
        "Return the full fixed source code."
    ),
    DefectClass.INCORRECT_ASSIGNMENT_OPERATOR: (
        "`{method_name}` uses an incorrect assignment (e.g., `+=` vs `=`).\n"
        "Correct the operator and return the updated code:\n```python\n{method_body}\n```"
    ),
    DefectClass.INCORRECT_OPERATOR: (
        "`{method_name}` contains an incorrect arithmetic/logical operator.\n"
        "Fix it and provide the entire corrected file:\n```python\n{method_body}\n```"
    ),
}
