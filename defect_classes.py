from enum import Enum

class DefectClass(Enum):
    MISSING_OR_ADDED_1 = 'missing/added +1'                
    INCORRECT_COMPARISON_OPERATOR = 'incorrect comparison operator'     
    INCORRECT_ARRAY_SLICE = 'incorrect array slice'            
    MISSING_CONDITION = 'missing condition'                
    MISSING_BASE_CASE = 'missing base case'                  
    INCORRECT_DATA_STRUCTURE_CONSTANT = 'incorrect data structure constant' 
    MISSING_FUNCTION_CALL = 'missing function call'             
    INCORRECT_METHOD_CALLED = 'incorrect method called'           
    INCORRECT_FIELD_DEREFERENCE = 'incorrect field dereference'        
    OFF_BY_ONE = 'off-by-one'                    
    INCORRECT_ASSIGNMENT_OPERATOR = 'incorrect assignment operator'    
    INCORRECT_OPERATOR ='incorrect operator'               
