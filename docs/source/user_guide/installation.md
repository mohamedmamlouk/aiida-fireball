# Installation Guide

This guide will help you install and set up the AiiDA Fireball plugin.

## Prerequisites

Before installing the AiiDA Fireball plugin, you need:

### 1. AiiDA Core

The plugin requires AiiDA 2.0 or later. Install AiiDA if you haven't already:

```bash
pip install aiida-core[atomic_tools]>=2.0.0
```

Or with conda:

```bash
conda install -c conda-forge aiida-core
```

For detailed AiiDA installation instructions, see the [AiiDA documentation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/install.html).

### 2. Fireball Code

You need a working installation of the Fireball code. Download and compile Fireball:

1. Visit the [Fireball website](http://fireball-dft.org)
2. Download the source code
3. Follow the compilation instructions for your system
4. Ensure the `fireball.x` executable is in your PATH or note its location

### 3. PostgreSQL Database

AiiDA requires a PostgreSQL database. Install PostgreSQL:

**Ubuntu/Debian:**
```bash
sudo apt-get install postgresql postgresql-client
```

**macOS:**
```bash
brew install postgresql
```

**Setup database:**
```bash
sudo -u postgres createuser -P aiida
sudo -u postgres createdb -O aiida aiida_db
```

## Installation Methods

### Method 1: From PyPI (Recommended)

Once the plugin is published, install directly from PyPI:

```bash
pip install aiida-fireball
```

### Method 2: From GitHub

Install the latest development version:

```bash
pip install git+https://github.com/ValkScripter/aiida-fireball.git
```

### Method 3: Development Installation

For plugin development:

```bash
git clone https://github.com/ValkScripter/aiida-fireball.git
cd aiida-fireball
pip install -e .
```

## Post-Installation Setup

### 1. Initialize AiiDA

If this is your first time using AiiDA:

```bash
verdi quicksetup
```

This will:
- Create an AiiDA profile
- Set up the database connection
- Start the daemon

### 2. Verify Installation

Check that the plugin is correctly installed:

```bash
verdi plugin list aiida.calculations
```

You should see `fireball` in the list of available calculation plugins.

### 3. Set Up Your Computer

Register your local computer with AiiDA:

```bash
verdi computer setup
```

Provide the following information:
- **Computer name**: `localhost`
- **Hostname**: `localhost`
- **Transport type**: `core.local`
- **Scheduler**: `core.direct`
- **Work directory**: `/tmp/aiida_work/`

Configure the computer:

```bash
verdi computer configure core.local localhost
```

### 4. Set Up the Fireball Code

Register your Fireball executable:

```bash
verdi code setup
```

Provide:
- **Label**: `fireball@localhost`
- **Default input plugin**: `fireball`
- **Computer**: `localhost`
- **Filepath executable**: `/path/to/your/fireball.x`

## Fdata Files Setup

Fireball requires Fdata files containing pseudopotentials and basis sets.

### 1. Download Fdata Files

Download the Fdata files from the Fireball website or obtain them from your system administrator.

### 2. Organize Fdata Directory

Create a directory structure like:

```
/path/to/fdata/
├── C/
│   ├── C.pp
│   └── C.na
├── H/
│   ├── H.pp
│   └── H.na
├── O/
│   ├── O.pp
│   └── O.na
└── ...
```

Each element should have its own subdirectory containing the `.pp` (pseudopotential) and `.na` (numerical atomic orbitals) files.

### 3. Register Fdata with AiiDA

Create a RemoteData node pointing to your Fdata directory:

```python
from aiida import orm

computer = orm.load_computer('localhost')
fdata_remote = orm.RemoteData()
fdata_remote.set_remote_path('/path/to/your/fdata')
fdata_remote.computer = computer
fdata_remote.store()

print(f"Fdata registered with PK: {fdata_remote.pk}")
```

## Verification

### Test Basic Functionality

Create a simple test script to verify everything works:

```python
from aiida import orm
from aiida.plugins import CalculationFactory, DataFactory

# Test plugin loading
FireballCalculation = CalculationFactory('fireball')
print("✓ Fireball calculation plugin loaded successfully")

# Test structure creation
StructureData = DataFactory('structure')
structure = StructureData()
structure.set_cell([[10, 0, 0], [0, 10, 0], [0, 0, 10]])
structure.append_atom(position=[0, 0, 0], symbols='H')
structure.append_atom(position=[0.74, 0, 0], symbols='H')
print("✓ Structure creation works")

# Test code loading
try:
    code = orm.load_code('fireball@localhost')
    print("✓ Fireball code configured correctly")
except:
    print("✗ Fireball code not found - check your code setup")

print("\nInstallation verification complete!")
```

### Run the Test

Save the script as `test_installation.py` and run:

```bash
python test_installation.py
```

## Troubleshooting

### Common Issues

#### 1. Plugin Not Found

```
Error: No plugin found for 'fireball'
```

**Solution:**
- Verify installation: `pip list | grep aiida-fireball`
- Check entry points: `verdi plugin list aiida.calculations`
- Reinstall if necessary: `pip install --force-reinstall aiida-fireball`

#### 2. Database Connection Issues

```
Error: could not connect to database
```

**Solution:**
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify connection: `psql -h localhost -U aiida aiida_db`
- Recreate profile if needed: `verdi profile delete <profile>` then `verdi quicksetup`

#### 3. Code Executable Not Found

```
Error: executable not found
```

**Solution:**
- Check path: `which fireball.x`
- Update code: `verdi code setup` with correct path
- Ensure permissions: `chmod +x /path/to/fireball.x`

#### 4. Fdata Files Not Found

```
Error: Cannot find Fdata files for element X
```

**Solution:**
- Check directory structure
- Verify file permissions
- Ensure both `.pp` and `.na` files exist for each element

### Getting Help

If you encounter issues:

1. Check the [AiiDA documentation](https://aiida.readthedocs.io)
2. Visit the [AiiDA Discourse forum](https://aiida.discourse.group)
3. Check the plugin's [GitHub issues](https://github.com/ValkScripter/aiida-fireball/issues)
4. Contact the developers: [email](mailto:mohamedmamlouk@example.com)

## Next Steps

After successful installation:

1. {doc}`user_guide/first_calculation`: Run your first Fireball calculation
2. {doc}`user_guide/transport_tutorial`: Learn about transport calculations
3. {doc}`examples/index`: Explore example calculations

## Development Setup

For plugin developers:

### Additional Dependencies

```bash
pip install -e .[dev]
```

This installs:
- `pytest` for testing
- `pre-commit` for code quality
- `black` for code formatting
- `isort` for import sorting
- `flake8` for linting

### Pre-commit Hooks

Set up pre-commit hooks:

```bash
pre-commit install
```

### Running Tests

Execute the test suite:

```bash
pytest tests/
```

### Building Documentation

Build documentation locally:

```bash
cd docs/
make html
```

The documentation will be available in `docs/build/html/`.

---

**Congratulations!** You now have the AiiDA Fireball plugin installed and ready to use.
