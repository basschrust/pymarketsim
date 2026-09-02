# config.py
import os
import sys
import yaml
import shutil
from datetime import datetime
from pathlib import Path


class Loader(yaml.SafeLoader):
    pass


def include_constructor(loader, node):
    filename = Path(loader.name).parent / loader.construct_scalar(node)

    with open(filename, "r") as f:
        return yaml.load(f, Loader)


Loader.add_constructor("!include", include_constructor)



# One directory per run
log_dir = datetime.now().strftime("run_%Y%m%d_%H%M%S")
output_dir = f"marketsim/output/{log_dir}"
os.makedirs(output_dir, exist_ok=True)
debug_logging = False

if len(sys.argv) > 1:
    src_file = f"marketsim/input/{sys.argv[1]}"
else:
    src_file = "marketsim/input/market_structure.yaml"

# Copy the configuration used for this run
shutil.copy2(
    src_file,
    f"{output_dir}/market_structure.yaml",
)

# with open(src_file) as f:
#     CONFIG = yaml.safe_load(f)

with open(src_file, "r") as f:
    Loader.name = src_file
    CONFIG = yaml.load(f, Loader)

