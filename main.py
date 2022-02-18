#!/usr/bin/env python

from argparse import ArgumentParser
from yaml import full_load
from fgt_transposer.exceptions import YAMLException
from fgt_transposer.parser import Parser
from fgt_transposer.write import write_config
from os import makedirs
import logging
import logging.config
from logging_config import logging_schema

# create directories
makedirs("_logs/", exist_ok=True)
makedirs("_backups/", exist_ok=True)

# setup logging
logging.config.dictConfig(logging_schema)
log_msg = logging.getLogger("priLogger")


def yaml_values(config_file) -> dict:
    """Open YAML and assign var cfg to file
    :param config_file: path of yaml file
    :return yaml dictionary
    """
    try:
        with open(config_file, mode="rt") as yfile:
            return full_load(yfile)
    except IOError:
        error = f"Config file: {config_file} is missing. Exiting.."
        log_msg.critical(error)
        raise YAMLException(error)


def argument_parser():
    """Parses command line arguments"""
    parser = ArgumentParser("Convert dst to src config", add_help=True)
    parser.add_argument(
        "--config_file", help="Yaml config file location.", default="config.yaml"
    )
    parser.add_argument("--dstconf", help="dst config file location.")
    parser.add_argument("--srcconf", help="src config file location.")
    parser.add_argument("--swapheaders", action="store_true")
    parser.add_argument("--logfile", help="Log file location.")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


def merged_arguments():
    """
    Take in argparse and yaml values. Prefer argparse over yaml.
    :param argparse and yaml output
    :return config_file location, arguments in dict format
    """
    args = argument_parser()
    cfg = yaml_values(args.config_file)
    config_file = args.config_file
    if args.dstconf:
        cfg["dstconf"] = args.dstconf
    if args.srcconf:
        cfg["srcconf"] = args.srcconf
    if args.swapheaders:
        cfg["swapheaders"] = args.swapheaders
    return config_file, cfg


def run_transpose_proc():
    (
        config_file,
        arguments,
    ) = merged_arguments()

    file_vars = Parser.return_files_as_vars(arguments)
    p = Parser(**file_vars)
    results = p.run_parse()
    write_config(*results)


if __name__ == "__main__":
    run_transpose_proc()
