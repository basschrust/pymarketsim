# config.py
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path


# make use of templates in market structure:
class IncludeLoader(yaml.SafeLoader):
    pass

def include_constructor(loader, node):
    relative_path = loader.construct_scalar(node)

    base_path = Path(loader.name).parent
    file_path = base_path / relative_path

    with open(file_path, "r") as f:
        sub_loader = IncludeLoader(f)
        sub_loader.name = str(file_path)
        return sub_loader.get_single_data()


IncludeLoader.add_constructor("!include", include_constructor)


# One directory per run
log_dir = datetime.now().strftime("run_%Y%m%d_%H%M%S")
output_dir = f"marketsim/output/{log_dir}"
os.makedirs(output_dir, exist_ok=True)
debug_logging = False

if len(sys.argv) > 1:
    src_file = f"marketsim/input/{sys.argv[1]}"
else:
    src_file = "marketsim/input/market_structure.yaml"


# Load and resolve all templates
with open(src_file, "r") as f:
    loader = IncludeLoader(f)
    loader.name = src_file
    CONFIG = loader.get_single_data()


# Save the fully resolved configuration used for this run
with open(f"{output_dir}/market_structure.yaml", "w") as f:
    yaml.safe_dump(
        CONFIG,
        f,
        sort_keys=False,
        default_flow_style=False,
    )

