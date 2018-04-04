"""
Tests the database wrappers
"""

import pytest
import numpy as np

# Import the DQM collection
import dqm_server as dserver
import dqm_client as dclient


@pytest.fixture(scope="module", params=["mongo"])
def db_socket(request):
    db_name = "dqm_local_values_test"
    db = dserver.db_socket_factory("127.0.0.1", 27017, db_name, db_type=request.param)

    # IP/port/drop table is specific to build
    if request.param == "mongo":
        if db_name in db.client.database_names():
            db.client.drop_database(db_name)
    else:
        raise KeyError("DB type %s not understood" % request.param)

    return db


def test_molecule_add(db_socket):

    water = dclient.data.get_molecule("water_dimer_minima.psimol")

    # Add once
    ret = db_socket.add_molecules(water.to_json())
    assert ret["nInserted"] == 1

    # Try duplicate adds
    ret = db_socket.add_molecules(water.to_json())
    assert ret["nInserted"] == 0
    assert ret["errors"][0] == (water.get_hash(), 11000)

    # Pull molecule from the DB for tests
    db_json = db_socket.get_molecule(water.get_hash())
    water_db = dclient.Molecule.from_json(db_json)
    water_db.compare(water)

    # Cleanup adds
    ret = db_socket.del_molecule_by_hash(water.get_hash())
    assert ret == 1


def test_molecule_add_many(db_socket):
    water = dclient.data.get_molecule("water_dimer_minima.psimol")
    water2 = dclient.data.get_molecule("water_dimer_stretch.psimol")

    ret = db_socket.add_molecules([water.to_json(), water2.to_json()])
    assert ret["nInserted"] == 2

    # Cleanup adds
    ret = db_socket.del_molecule_by_hash([water.get_hash(), water2.get_hash()])
    assert ret == 2