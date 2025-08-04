Getting Started
===============

This guide will help you get up and running with AiiDA Fireball.

Prerequisites
-------------

Before installing AiiDA Fireball, make sure you have:

- Python 3.8 or higher
- AiiDA 2.0 or higher installed and configured
- Access to a computer with Fireball installed

Installation
------------

Install from PyPI (when available)::

    pip install aiida-fireball

Or install from source::

    git clone https://github.com/mohamedmamlouk/aiida-fireball.git
    cd aiida-fireball
    pip install -e .

Verify the installation::

    verdi plugin list aiida_fireball

Setting up AiiDA
-----------------

If you haven't set up AiiDA yet, run::

    verdi quicksetup

This will create a default profile for you.

Configuring a Computer
----------------------

Setup your computer where Fireball is installed::

    verdi computer setup

Follow the prompts to configure:

- Computer name (e.g., "localhost")
- Hostname
- Transport type (usually "core.local" or "core.ssh")
- Scheduler type (e.g., "core.direct" or "core.slurm")
- Work directory path

Configure the computer::

    verdi computer configure <TRANSPORT> <COMPUTER_NAME>

Test the connection::

    verdi computer test <COMPUTER_NAME>

Setting up the Fireball Code
-----------------------------

Setup the Fireball executable::

    verdi code setup

Configure:

- Label: "fireball" (or any name you prefer)
- Plugin: "fireball.fireball"
- Computer: select your configured computer
- Remote absolute path: path to Fireball executable (e.g., "/usr/local/bin/fireball.x")

Your First Calculation
----------------------

Create a simple Python script::

    from aiida import orm, load_profile
    from aiida.engine import submit
    from aiida_fireball import FireballCalculation

    # Load your AiiDA profile
    load_profile()

    # Create a simple structure (water molecule)
    structure = orm.StructureData()
    structure.append_atom(position=(0.0, 0.0, 0.0), symbols='O')
    structure.append_atom(position=(0.757, 0.587, 0.0), symbols='H')
    structure.append_atom(position=(-0.757, 0.587, 0.0), symbols='H')
    structure.set_cell([10.0, 10.0, 10.0])

    # Set calculation parameters
    parameters = orm.Dict(dict={
        'max_scf_iterations': 100,
        'scf_tolerance': 1e-6,
        'charge': 0,
        'spin': 1
    })

    # Setup calculation
    builder = FireballCalculation.get_builder()
    builder.structure = structure
    builder.parameters = parameters
    builder.code = orm.load_code('fireball@localhost')  # Adjust the code name
    
    # Submit the calculation
    calc = submit(builder)
    print(f"Submitted calculation with PK: {calc.pk}")

Run the script and wait for the calculation to complete. You can check the status with::

    verdi process list

Analyzing Results
-----------------

Once your calculation is finished, you can analyze the results::

    from aiida import orm, load_profile
    
    load_profile()
    
    # Load your calculation (replace CALC_PK with actual PK)
    calc = orm.load_node(CALC_PK)
    
    # Check if successful
    if calc.is_finished_ok:
        results = calc.outputs.output_parameters.get_dict()
        print(f"Total energy: {results['total_energy']} eV")
    else:
        print("Calculation failed")

Next Steps
----------

- Learn about transport calculations in the :doc:`tutorial`
- Explore the :doc:`../developer_guide/index` for advanced usage
- Check out the examples in the main documentation
