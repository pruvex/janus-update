# A.py - Module A imports B (creating circular dependency)
import B

def function_a():
    return "Function A called"

if __name__ == "__main__":
    print(function_a())
    print(B.function_b())
