from pratt_parser import calc
assert calc("2 + 3") == 5
assert calc("2 + 3 * 4") == 14
assert calc("(2 + 3) * 4") == 20
assert calc("2 ^ 3 ^ 2") == 512  # right-assoc: 2^(3^2)=2^9=512
assert abs(calc("sqrt(16)") - 4) < 0.01
assert calc("3 > 2") == True
print("Pratt parser tests passed")