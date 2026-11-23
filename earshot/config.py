import yaml

from earshot import ROOT

CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
