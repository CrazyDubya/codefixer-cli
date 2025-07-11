import os,sys
from pathlib import Path

def test_function(  x,y  ):
    """Test function with bad formatting."""
    a=1
    b=2
    if a==b:
        print("equal")
    return a+b

class TestClass:
    def __init__(self):
        self.value = None
    
    def method_with_long_line_that_exceeds_the_maximum_line_length_and_should_trigger_a_linting_error(self):
        pass

# Unused import
import json

# Missing newline at end of file 