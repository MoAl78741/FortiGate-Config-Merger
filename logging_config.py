from datetime import date

# Ref: https://scicomp.ethz.ch/public/manual/Python/3.4.3/howto-logging-cookbook.pdf

logs_target = "_logs/logfile_" + str(date.today()) + ".log"

logging_schema = {
    "version": 1,
    "formatters": {
        "standard": {
            "class": "logging.Formatter",
            "format": "%(levelname)s | %(name)s | %(asctime)s | %(message)s",
            "datefmt": "%m/%d/%Y %I:%M:%S %p",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "DEBUG",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "level": "INFO",
            "filename": logs_target,
            "mode": "a",
            "encoding": "utf-8",
            "maxBytes": 500000,
            "backupCount": 4,
        },
    },
    "loggers": {
        "priLogger": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}
