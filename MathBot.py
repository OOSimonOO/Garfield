from os import replace
from string import digits
import math

functions = {"abs" : abs, "round" : round, "pow" : math.pow, "sqrt" : math.sqrt, "sin" : math.sin, "asin" : math.asin, "cos" : math.cos, "acos" : math.acos, "tan" : math.tan, "atan" : math.atan, "atan2" : math.atan2, "deg" : math.degrees, "rad" : math.radians}
std_variables = {"pi" : math.pi, "e" : math.e, "j" : 1j}
variables = {}


def calculate_string(equation : str):
    equation = equation.lower()
    if "\n" in equation:
        return 0, False, "There is a linebreak in the equation"
    if "\"" in equation:
        return 0, False, "There is a \" in the equation"
    if "\'" in equation:
        return 0, False, "There is a \' in the equation"
    
    #hex -> dec
    while True:
        pos = equation.find("0x")
        if pos == -1:
            break
        hex_number = "0x"
        num = 0
        for c in equation[pos+2:]:
            if c in digits + "abcdef":
                hex_number += c
            else:
                break
        if hex_number != "0x":
            num = int(hex_number, 16)
        equation = equation.replace(hex_number, str(num))

    #oct -> dec
    while True:
        pos = equation.find("0o")
        if pos == -1:
            break
        oct_number = "0o"
        num = 0
        for c in equation[pos+2:]:
            if c in "01234567":
                oct_number += c
            else:
                break
        if oct_number != "0o":
            num = int(oct_number, 8)
        equation = equation.replace(oct_number, str(num))
        
              
    #bin -> dec
    while True:
        pos = equation.find("0b")
        if pos == -1:
            break
        bin_number = "0b"
        num = 0
        for c in equation[pos+2:]:
            if c in "01":
                bin_number += c
            else:
                break
        if bin_number != "0b":
            num = int(bin_number, 2)
        equation = equation.replace(bin_number, str(num))
         
        
    
    undef_funktions = []
    name = ""
    for c in equation:
        if c in list(digits) + ["+", "-", "*", "/", "%", ".", ",", " ", "(", ")"]:
            if not name in list(functions) + list(std_variables) + list(variables) + [""]:
                undef_funktions.append(name)
            name = ""
        else:
            name += c

    if len(undef_funktions) > 0:
        return 0, False, f"There are undefined functions {undef_funktions}"
    try:
        fields = {}
        fields.update(functions)
        fields.update(std_variables)
        fields.update(variables)
        result = eval(equation, {}, fields)
    except Exception as e:
        return 0, False, str(e)
    if not type(result) in [int, float, complex]:
        return 0, False, "The result have to be int, float or complex"
    return result, True, ""
