# config.py
import os
import yaml
import shutil
from datetime import datetime

# One directory per run
log_dir = datetime.now().strftime("run_%Y%m%d_%H%M%S")
output_dir = f"marketsim/output/{log_dir}"
os.makedirs(output_dir, exist_ok=True)
debug_logging = False

# Copy the configuration used for this run
shutil.copy2(
    "marketsim/input/market_structure.yaml",
    f"{output_dir}/market_structure.yaml",
)

with open("marketsim/input/market_structure.yaml") as f:
    CONFIG = yaml.safe_load(f)

