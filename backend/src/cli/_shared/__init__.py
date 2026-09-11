"""
Infrastructure the CLI commands share -- never a command itself.

THE UNDERSCORE IS THE CONVENTION, matching _common.py in the
connections domain: it marks a module as something the siblings around
it lean on, so that `flask --help` listing nothing from here is the
expected result rather than a bug somebody goes looking for.
"""
