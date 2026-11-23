import json
from pathlib import Path
from securesystemslib.keys import generate_ed25519_key
from tuf.api.metadata import (
    Root,
    Targets,
    Key,
    Role,
)
from tuf.api.serialization.json import JSONSerializer


def generate_metadata(version: str, target_file: str):
    # Configurar rol ROOT
    root = Root(expires="2030-01-01T00:00:00Z",
                version=1, spec_version="1.0.0")

    # Generar claves
    root_key = Key.generate("ed25519")
    targets_key = Key.generate("ed25519")

    # Añadir claves y roles
    root.add_key(root_key, "root")
    root.add_key(targets_key, "targets")
    root.roles = {
        "root": Role([root_key.keyid], threshold=1),
        "targets": Role([targets_key.keyid], threshold=1),
    }

    # Configurar TARGETS
    targets = Targets(expires="2030-01-01T00:00:00Z", version=1)
    targets.add_target("lece-app-v1.0.0.tar.gz", {"version": "1.0.0"})

    # Firmar y guardar
    root.sign(root_key)
    targets.sign(targets_key)
    root.to_file("tuf-metadata/root.json", JSONSerializer())
    targets.to_file("tuf-metadata/targets.json", JSONSerializer())
