import logging

def set_logger(name, log_file):
    l = logging.getLogger(name)
    filehandler = logging.FileHandler(log_file, mode='w')
    filehandler.setLevel(0)
    streamhandler = logging.StreamHandler()
    l.setLevel(logging.DEBUG)
    l.addHandler(filehandler)
    l.addHandler(streamhandler)