# B.py - Module B imports C (continuing circular chain)
import C

def function_b():
    return "Function B called"

if __name__ == "__main__":
    print(function_b())
    print(C.function_c())
