# C.py - Module C imports A (completing the circular loop)
import A

def function_c():
    return "Function C called"

if __name__ == "__main__":
    print(function_c())
    print(A.function_a())
