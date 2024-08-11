import logging
import os
import datetime as dt
import pytz

def get_logger(file_name):
    # get logs path as current files path
    logs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),"logs")
    
    print(logs_path)
    if not os.path.exists(logs_path):
        os.makedirs(logs_path)

    tz = pytz.timezone('Asia/Kolkata')
    tz_abbreviation = dt.datetime.now(tz=tz).strftime('%Z')
    logging.Formatter.converter = lambda *args: dt.datetime.now(tz=tz).timetuple()
    formatter = logging.Formatter('[%(asctime)s '+tz_abbreviation+'][%(filename)s :%(lineno)4s][%(levelname)8s] ~ %(message)s',"%Y-%m-%d %H:%M:%S")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(filename= os.path.join(logs_path,f"{file_name}_{dt.datetime.now(tz=pytz.timezone('Asia/Kolkata')).strftime('%Y_%m_%d')}.log"),mode="a")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    try:
        if len(logger.handlers) > 0:
            logger.removeHandler(file_handler)
            logger.removeHandler(console_handler)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    except:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger