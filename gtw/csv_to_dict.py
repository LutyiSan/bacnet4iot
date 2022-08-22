import pandas as pd
from loguru import logger

PREFIX = "gtw/devices/"
def get_device_dict(file):
    try:
        device_dict = pd.read_csv(f"{PREFIX}{file}", delimiter=";", index_col=False).to_dict('list')
        return device_dict
    except Exception as e:
        logger.exception(f"FAIL read csv{file}", e)
        return False


