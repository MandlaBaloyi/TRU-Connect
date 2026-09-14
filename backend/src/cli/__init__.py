"""
Command-line operations, for work that has no screen yet.

THE ADMIN CONTROL CENTRE IS DEFERRED (V2_09 Part 7), and the catalogue
review queue cannot wait for it -- the queue gates whether suppliers can
be onboarded at all. So the decisions happen here for now.

THE RULE THESE COMMANDS OBEY: they call the SERVICE layer, never raw
SQL. A human changing rows by hand with no trail is how you end up
unable to answer "who approved this, and when" -- which is precisely the
question asked after something goes wrong, and the reason the audit
domain exists. When the control centre arrives it calls the same
services and these commands keep working unchanged.
"""
from __future__ import annotations

from flask import Flask


def register_cli(app: Flask) -> None:
    from src.cli.commands.admin import admin_cli
    from src.cli.commands.catalogue import catalogue_cli
    from src.cli.commands.demand import demand_cli
    from src.cli.commands.verification import verification_cli

    app.cli.add_command(admin_cli)
    app.cli.add_command(catalogue_cli)
    app.cli.add_command(demand_cli)
    app.cli.add_command(verification_cli)
