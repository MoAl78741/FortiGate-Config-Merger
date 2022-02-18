from fgt_transposer.exceptions import BackupException
from os import path
import logging

log_msg = logging.getLogger(f"priLogger.{__name__}")


def write_config(newfile_name, files):
    with open(newfile_name, "w") as nn:
        newfile = files
        lst_of_keys = newfile.keys()
        for i in lst_of_keys:
            for line in newfile[i]:
                nn.write(line)

    if not path.exists(newfile_name):
        raise_exception(BackupException, f"Unable to backup file {newfile_name}")
    log_msg.info(f"Successfully backed up config for {newfile_name} ")
