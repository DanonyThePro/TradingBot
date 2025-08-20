import os
import sys

try:
    # Find site-packages dynamically
    site_packages = next(p for p in sys.path if p.endswith("site-packages"))
    target_file = os.path.join(site_packages, "pandas_ta/momentum/squeeze_pro.py")

    with open(target_file, "r") as f:
        code = f.read()

    # Fix the wrong import
    code = code.replace("from numpy import NaN as npNaN", "from numpy import nan as npNaN")

    with open(target_file, "w") as f:
        f.write(code)

    print("✅ Fixed pandas_ta momentum/squeeze_pro.py import!")
except Exception as e:
    print("⚠️ Patch failed:", e)
