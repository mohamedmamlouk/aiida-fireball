# AiiDA Fireball Plugin

[![Build Status](https://github.com/yourusername/aiida-fireball/workflows/ci/badge.svg)](https://github.com/yourusername/aiida-fireball/actions)
[![Coverage Status](https://coveralls.io/repos/github/yourusername/aiida-fireball/badge.svg?branch=main)](https://coveralls.io/github/yourusername/aiida-fireball?branch=main)
[![PyPI version](https://badge.fury.io/py/aiida-fireball.svg)](https://badge.fury.io/py/aiida-fireball)
[![Python version](https://img.shields.io/pypi/pyversions/aiida-fireball.svg)](https://pypi.org/project/aiida-fireball)

AiiDA plugin for the Fireball semi-empirical DFT-based electronic structure code with advanced transport calculations.

## Features

- **Fireball Calculations**: Full support for semi-empirical DFT calculations
- **Transport Properties**: Advanced transport calculations with optional files
  - `interaction.optional` - Interaction parameters
  - `eta.optional` - Eta parameters  
  - `trans.optional` - Transport parameters
  - `bias.optional` - Bias voltage parameters
- **Flexible Input Generation**: Generate any combination of optional transport files
- **Birch-Murnaghan Fitting**: Automated equation of state calculations
- **AiiDA Integration**: Full compatibility with AiiDA 2.0+ ecosystem

## Installation

### Prerequisites

- Python 3.8+
- AiiDA 2.0+
- Fireball code installed on your system

### Install from PyPI

```bash
pip install aiida-fireball
```

### Install from Source

```bash
git clone https://github.com/mohamedmamlouk/aiida-fireball.git
cd aiida-fireball
pip install -e .
```

### Verify Installation

```bash
verdi plugin list aiida.calculations
# Should show: fireball
```

## Quick Start

### 1. Set up Computer and Code

```python
from aiida import orm
from aiida.engine import submit

# Create computer
computer = orm.Computer(
    label='localhost',
    hostname='localhost',
    transport_type='local',
    scheduler_type='direct'
)
computer.store()
computer.configure()

# Create code
code = orm.Code(
    input_plugin_name='fireball',
    remote_computer_exec=[computer, '/path/to/fireball.x']
)
code.label = 'fireball-v3.0'
code.store()
```

### 2. Basic Calculation

```python
from aiida.plugins import CalculationFactory, DataFactory
from aiida.engine import submit

# Load plugins
FireballCalculation = CalculationFactory('fireball')
StructureData = DataFactory('structure')

# Create structure (example: H2 molecule)
structure = StructureData()
structure.set_cell([[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]])
structure.append_atom(position=[0.0, 0.0, 0.0], symbols='H')
structure.append_atom(position=[0.74, 0.0, 0.0], symbols='H')

# Set up inputs
inputs = {
    'code': code,
    'structure': structure,
    'metadata': {
        'options': {
            'resources': {'num_machines': 1},
            'max_wallclock_seconds': 1800,
        }
    }
}

# Submit calculation
calc_node = submit(FireballCalculation, **inputs)
print(f"Calculation submitted with PK={calc_node.pk}")
```

### 3. Transport Calculations

```python
# Transport calculation with all optional files
transport_inputs = {
    'code': code,
    'structure': structure,
    'kpoints': kpoints,
    'fdata_remote': fdata_remote,
    'parameters': orm.Dict(dict={
        'OPTION': {
            'iimage': 1,  # single point calculation
        },
        'OUTPUT': {
            'iwrtpop': 1,
        }
    }),
    'settings': orm.Dict(dict={
        'TRANSPORT': {
            'INTERACTION': {
                'ncell1': 0,
                'total_atoms1': 5,
                'ninterval1': 1,
                'intervals1': [[1, 5]],
                'natoms_tip1': 2,
                'atoms1': [1, 2],
                'ncell2': 0,
                'total_atoms2': 5,
                'ninterval2': 1,
                'intervals2': [[4, 5]],
                'natoms_tip2': 2,
                'atoms2': [4, 5]
            },
            'ETA': {
                'imag_part': 0.01,
                'intervals': [[1, 2], [4, 5]]
            },
            'TRANS': {
                'ieta': True,
                'iwrt_trans': True,
                'ichannel': False,
                'ifithop': 1,
                'Ebottom': -2.0,
                'Etop': 2.0,
                'nsteps': 100,
                'eta': 0.01
            },
            'BIAS': {
                'bias': 1.0,
                'z_top': 10.0,
                'z_bottom': 0.0
            }
        }
    }),
    'metadata': {
        'options': {
            'resources': {'num_machines': 1},
            'max_wallclock_seconds': 3600,
        }
    }
}

calc_node = submit(FireballCalculation, **transport_inputs)
```

### 4. Advanced Parallel Calculations

For high-throughput surface calculations with charge state variations:

```python
# Generate W(110) surface with ASE
from ase.build import bcc110
slab = bcc110('W', size=(1,1,15), a=3.1652, vacuum=20.0)
structure = StructureData(ase=slab)

# Submit parallel calculations for different charge states
qstates = [0, 0.0078, 0.0156, 0.0233, 0.0311, 0.0389, 0.0467, 0.0545]

for q in qstates:
    params = {
        "OPTION": {
            "nstepi": 1, "nstepf": 5000, "icluster": 0,
            "iquench": -1, "dt": 0.25, "qstate": q
        },
        "OUTPUT": {"iwrtxyz": 0, "iwrtdos": 0}
    }
    
    builder = FireballCalculation.get_builder()
    builder.code = code
    builder.structure = structure
    builder.parameters = Dict(dict=params)
    builder.fdata_remote = fdata_remote
    builder.metadata.label = f"W110_q{q}"
    
    # HPC optimization
    builder.metadata.options.prepend_text = """
# Fix qstate formatting
sed -i "s/\\(qstate *= *\\)'\\([0-9.]*d0\\)'/\\1\\2/" fireball.in
"""
    
    calc = submit(builder)
    print(f"qstate={q} → PK={calc.pk}")
```

See [`examples/submit_qstate_parallel.py`](examples/submit_qstate_parallel.py) for the complete example.

## Documentation

Full documentation is available at [ReadTheDocs](https://aiida-fireball.readthedocs.io/).

- [Installation Guide](https://aiida-fireball.readthedocs.io/en/latest/user_guide/get_started.html)
- [Tutorial](https://aiida-fireball.readthedocs.io/en/latest/user_guide/tutorial.html)
- [API Reference](https://aiida-fireball.readthedocs.io/en/latest/developer_guide/index.html)

## Examples

See the `examples/` directory for complete working examples:

- `examples/basic_calculation.py` - Simple molecular calculation
- `examples/transport_calculation.py` - Transport properties calculation
- `examples/birch_murnaghan.py` - Equation of state workflow

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/calculations/test_fireball.py

# Run with coverage
pytest --cov=aiida_fireball --cov-report=html
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
git clone https://github.com/mamloukmohamed/aiida-fireball.git
cd aiida-fireball
pip install -e .[dev]
pre-commit install
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this plugin in your research, please cite:

```bibtex
@misc{aiida_fireball,
  title={AiiDA Fireball Plugin},
  author={mohamedmamlouk},
  year={2024},
  url={https://github.com/mohamedmamlouk/aiida-fireball}
}
```

## Support

- Documentation: https://aiida-fireball.readthedocs.io/
- Issues: https://github.com/mohamedmamlouk/aiida-fireball/issues
- Discussions: https://github.com/mohamedmamlouk/aiida-fireball/discussions
- AiiDA Community: https://aiida.net/
