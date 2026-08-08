from kgm.cli.app import app
from kgm.cli.commands.label import app as label_app
from kgm.cli.commands.validate import validate_command

app.add_typer(label_app, name="label")

from kgm.cli.commands.document import app as document_app

app.add_typer(document_app, name="document")

from kgm.cli.commands.load import app as load_app

app.add_typer(load_app, name="load")

from kgm.cli.commands.event.cli import event_app
from kgm.cli.commands.sync import sync_command

app.add_typer(event_app)
