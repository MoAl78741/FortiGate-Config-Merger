import logging

log_msg = logging.getLogger(f"priLogger.{__name__}")


class YAMLException(Exception):
    pass


class BackupException(Exception):
    pass


class SectionOrVdomException(Exception):
    pass