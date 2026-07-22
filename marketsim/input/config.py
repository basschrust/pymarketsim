# config.py
import yaml

with open("marketsim/input/market_structure.yaml") as f:
    CONFIG = yaml.safe_load(f)
