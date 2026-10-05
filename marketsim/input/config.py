# config.py
import os
import sys
import yaml
import random
import numpy as np
from datetime import datetime
from pathlib import Path


DEFAULT_CONFIG = "market_structure.yaml"


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


# Load and resolve all templates

def load_config(filename: str = DEFAULT_CONFIG) -> dict:
    src_file = Path("marketsim/input") / filename

    with open(src_file, "r") as f:
        loader = IncludeLoader(f)
        loader.name = src_file
        config = loader.get_single_data()

    random.seed(config.get("seed", 67))
    np.random.seed(config.get("seed", 67))
    # TODO: save seed in DB

    # Save the fully resolved configuration used for this run
    with open(f"{output_dir}/market_structure.yaml", "w") as f:
        yaml.safe_dump(
            config,
            f,
            sort_keys=False,
            default_flow_style=False,
        )

    return config

