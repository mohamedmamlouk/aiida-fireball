# AiiDA Fireball Plugin

![Fireball Structure](docs/source/_static/fireball_structure.png)

[![Build Status](https://github.com/mohamedmamlouk/aiida-fireball/workflows/ci/badge.svg)](https://github.com/mohamedmamlouk/aiida-fireball/actions)
[![PyPI version](https://img.shields.io/pypi/v/aiida-fireball.svg)](https://pypi.org/project/aiida-fireball/)
[![Python versions](https://img.shields.io/pypi/pyversions/aiida-fireball.svg)](https://pypi.org/project/aiida-fireball/)
[![Documentation Status](https://readthedocs.org/projects/aiida-fireball/badge/?version=latest)](https://aiida-fireball.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/github/license/mohamedmamlouk/aiida-fireball.svg)](https://github.com/mohamedmamlouk/aiida-fireball/blob/main/LICENSE)

**AiiDA plugin for Fireball semi-empirical DFT calculations** - Simple, efficient, and well-integrated with the AiiDA ecosystem.

## 🚀 Key Features

- **Full Fireball Integration**: Complete support for semi-empirical DFT calculations
- **Advanced Transport**: State-of-the-art transport property calculations
- **Simple API**: Easy-to-use interface similar to AiiDA Quantum ESPRESSO
- **High-Throughput Ready**: Designed for large-scale computational studies
- **Well Documented**: Comprehensive documentation with examples

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

## 📖 Quick Start

Get up and running in minutes! Here's a simple silicon calculation:

```python
from ase.build import bulk
from aiida.plugins import DataFactory, CalculationFactory
from aiida.engine import submit
from aiida import orm

# Create silicon structure with ASE
StructureData = DataFactory('core.structure')
si_ase = bulk('Si', 'diamond', a=5.43)
structure = StructureData(ase=si_ase)

# Basic parameters
parameters = orm.Dict({
    'OPTION': {
        'iimage': 1,        # Single point calculation
        'iquench': 0,       # No optimization
        'dt': 0.25,         # Time step
        'nstepf': 1,        # Number of steps
        'ifixcharges': 1,   # Fix atomic charges
    },
    'OUTPUT': {
        'iwrtdos': 0,       # Don't write DOS
        'iwrtxyz': 1,       # Write position trajectory
    }
})

# Submit calculation
FireballCalculation = CalculationFactory('fireball')
calc_node = submit(FireballCalculation,
    code=orm.load_code('fireball@localhost'),
    structure=structure,
    parameters=parameters,
    kpoints=kpoints,  # 4x4x4 mesh
    fdata_remote=fdata_remote,
    metadata={'options': {'resources': {'num_machines': 1}}}
)

print(f"Calculation submitted: PK={calc_node.pk}")
```

For detailed tutorials, see our [**📚 Documentation**](https://aiida-fireball.readthedocs.io/).
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
# Status check
