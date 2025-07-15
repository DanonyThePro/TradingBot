import os

try:
    site_packages = "/opt/render/project/src/.venv/lib/python3.13/site-packages/pandas_ta/momentum"
    target_file = os.path.join(site_packages, "squeeze_pro.py")

    with open(target_file, "r") as f:
        code = f.read()

    # Fix import line
    code = code.replace("from numpy import NaN as npNaN", "from numpy import nan as npNaN")

    with open(target_file, "w") as f:
        f.write(code)

    print("Fixed pandas_ta momentum/squeeze_pro.py import!")
except Exception as e:
    print(e)