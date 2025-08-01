# API Reference

This section provides detailed reference documentation for all components of the AiiDA Fireball plugin.

```{eval-rst}
.. automodule:: aiida_fireball
   :members:
   :undoc-members:
   :show-inheritance:
```

## Calculations

### FireballCalculation

```{eval-rst}
.. autoclass:: aiida_fireball.calculations.fireball.FireballCalculation
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
```

#### Input Specifications

The `FireballCalculation` class accepts the following inputs:

```{eval-rst}
.. automethod:: aiida_fireball.calculations.fireball.FireballCalculation.define
```

### Utility Functions

```{eval-rst}
.. automodule:: aiida_fireball.calculations.utils
   :members:
   :undoc-members:
   :show-inheritance:
```

## Parsers

### FireballParser

```{eval-rst}
.. autoclass:: aiida_fireball.parsers.fireball.FireballParser
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
```

### RawParser

```{eval-rst}
.. autoclass:: aiida_fireball.parsers.raw.RawParser
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
```

## Workflows

### BirchMurnaghanRelaxWorkChain

```{eval-rst}
.. autoclass:: aiida_fireball.workflows.birch_murnaghan_relax.BirchMurnaghanRelaxWorkChain
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
```

## Data Types

The plugin uses standard AiiDA data types with specific conventions:

### StructureData

Standard AiiDA `StructureData` for atomic structures. See [AiiDA documentation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/reference/apidoc/aiida.orm.nodes.data.html#aiida.orm.nodes.data.structure.StructureData).

### Dict (Parameters)

Parameters are specified using AiiDA `Dict` nodes with the following structure:

```python
parameters = {
    'OPTION': {
        'iimage': 1,      # Calculation type
        'iquench': 0,     # Optimization method
        'dt': 0.5,        # Time step
        'nstepf': 100,    # Number of steps
    },
    'OUTPUT': {
        'iwrtpop': 1,     # Population analysis
        'iwrtdos': 1,     # Density of states
        'iwrtatom': 1,    # Atomic information
    }
}
```

### Settings (Transport Parameters)

Transport calculations use the `settings` input with `TRANSPORT` namespace:

```python
transport_settings = {
    'TRANSPORT': {
        'INTERACTION': {
            'ncell1': 0,
            'total_atoms1': 5,
            # ... other interaction parameters
        },
        'ETA': {
            'imag_part': 0.01,
            # ... other eta parameters
        },
        'TRANS': {
            'ieta': True,
            'Ebottom': -2.0,
            'Etop': 2.0,
            # ... other transport parameters
        },
        'BIAS': {
            'bias': 1.0,
            'z_top': 10.0,
            'z_bottom': 0.0
        }
    }
}
```

### KpointsData

Standard AiiDA `KpointsData` for k-point sampling. See [AiiDA documentation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/reference/apidoc/aiida.orm.nodes.data.html#aiida.orm.nodes.data.array.kpoints.KpointsData).

### RemoteData (Fdata)

`RemoteData` pointing to directory containing Fireball Fdata files:

```python
fdata_remote = orm.RemoteData()
fdata_remote.set_remote_path('/path/to/fdata')
fdata_remote.computer = computer
```

The Fdata directory should contain subdirectories for each element with `.pp` and `.na` files.

## Entry Points

The plugin registers the following entry points:

### Calculations

- `fireball`: Main Fireball calculation class

### Parsers

- `fireball`: Default Fireball output parser
- `fireball.raw`: Raw file parser

### Workflows

- `fireball.birch_murnaghan_relax`: Birch-Murnaghan equation of state workflow

## Constants and Utilities

### Physical Constants

```{eval-rst}
.. autodata:: aiida_fireball.calculations.utils.BOHR_TO_ANGSTROM
   :annotation: = 0.52917721067

.. autodata:: aiida_fireball.calculations.utils.RY_TO_EV  
   :annotation: = 13.605693009
```

### File Templates

The plugin includes templates for generating Fireball input files:

```{eval-rst}
.. autofunction:: aiida_fireball.calculations.fireball.FireballCalculation._generate_input_file

.. autofunction:: aiida_fireball.calculations.fireball.FireballCalculation._generate_interaction_optional

.. autofunction:: aiida_fireball.calculations.fireball.FireballCalculation._generate_eta_optional

.. autofunction:: aiida_fireball.calculations.fireball.FireballCalculation._generate_trans_optional

.. autofunction:: aiida_fireball.calculations.fireball.FireballCalculation._generate_bias_optional
```

## Error Handling

The plugin defines several custom exceptions:

```{eval-rst}
.. autoexception:: aiida_fireball.calculations.fireball.FireballCalculationError

.. autoexception:: aiida_fireball.parsers.fireball.FireballParserError
```

## Version Information

```{eval-rst}
.. autodata:: aiida_fireball.__version__
   :annotation: Plugin version string
```

## Plugin Metadata

```{eval-rst}
.. autodata:: aiida_fireball.__author__
   :annotation: Plugin authors

.. autodata:: aiida_fireball.__email__
   :annotation: Contact email
```
