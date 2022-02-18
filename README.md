# FortiGate-Config-Merger
## Synopsis

Merges specific sections of one FortiGate config file into another FortiGate config file.

## Purpose

This can be useful tool for adapting prod configs to a lab environment for testing.

## What the app does:

- Parses command lines arguments and YAML config file. CLI args overwrite YAML args.
- Splits configuration into dictionaries.
- Parses YAML for start and end lines that refer to sections of the configuration.
- Does a find and replace for those sections of the config.
- Produces a new configuration <original_name>_transposed.conf that can be uplaoded to FortiGate.