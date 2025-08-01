# Examples Gallery

This section contains practical examples demonstrating various features of the AiiDA Fireball plugin.

## Basic Examples

### Single Point Calculation

A simple single-point energy calculation for a water molecule:

```{literalinclude} ../../../examples/basic_calculation.py
:language: python
:caption: Basic single-point calculation
```

### Geometry Optimization  

Optimize the geometry of a molecular system:

```{literalinclude} ../../../examples/optimization.py
:language: python  
:caption: Geometry optimization example
```

## Transport Calculations

### Simple Transport

Basic transport calculation setup:

```{literalinclude} ../../../examples/transport_calculation.py
:language: python
:caption: Transport calculation example
```

### Advanced Transport

More complex transport calculation with all optional files:

```python
from aiida import orm
from aiida.plugins import CalculationFactory, DataFactory
from aiida.engine import submit

# Set up structure (molecular junction)
StructureData = DataFactory('structure')
structure = StructureData()
structure.set_cell([[20.0, 0.0, 0.0], [0.0, 15.0, 0.0], [0.0, 0.0, 15.0]])

# Create a benzene molecule
positions = [
    [0.0, 1.4, 0.0],      # C
    [1.212, 0.7, 0.0],    # C  
    [1.212, -0.7, 0.0],   # C
    [0.0, -1.4, 0.0],     # C
    [-1.212, -0.7, 0.0],  # C
    [-1.212, 0.7, 0.0],   # C
    [0.0, 2.48, 0.0],     # H
    [2.148, 1.24, 0.0],   # H
    [2.148, -1.24, 0.0],  # H
    [0.0, -2.48, 0.0],    # H
    [-2.148, -1.24, 0.0], # H
    [-2.148, 1.24, 0.0],  # H
]

symbols = ['C'] * 6 + ['H'] * 6

for pos, symbol in zip(positions, symbols):
    structure.append_atom(position=pos, symbols=symbol)

structure.store()

# Comprehensive transport parameters
transport_settings = {
    'TRANSPORT': {
        'INTERACTION': {
            'ncell1': 0, 'total_atoms1': 6, 'ninterval1': 1,
            'intervals1': [[1, 3]], 'natoms_tip1': 2, 'atoms1': [1, 2],
            'ncell2': 0, 'total_atoms2': 6, 'ninterval2': 1, 
            'intervals2': [[4, 6]], 'natoms_tip2': 2, 'atoms2': [5, 6]
        },
        'ETA': {
            'imag_part': 0.01,
            'intervals': [[1, 3], [4, 6]]
        },
        'TRANS': {
            'ieta': True, 'iwrt_trans': True, 'ichannel': True,
            'ifithop': 1, 'Ebottom': -3.0, 'Etop': 3.0, 
            'nsteps': 200, 'eta': 0.01
        },
        'BIAS': {
            'bias': 0.5, 'z_top': 8.0, 'z_bottom': -8.0
        }
    }
}

# Calculation parameters
parameters = {
    'OPTION': {
        'iimage': 1,
        'iquench': 0,
        'dt': 0.5,
        'nstepf': 1,
    },
    'OUTPUT': {
        'iwrtpop': 1,
        'iwrttrans': 1,
        'iwrtdos': 1,
    }
}

# Set up and submit
FireballCalculation = CalculationFactory('fireball')
code = orm.load_code('fireball@localhost')

inputs = {
    'code': code,
    'structure': structure,
    'parameters': orm.Dict(dict=parameters),
    'kpoints': kpoints,  # Define as needed
    'fdata_remote': fdata_remote,  # Define as needed
    'settings': orm.Dict(dict=transport_settings),
    'metadata': {
        'label': 'benzene_transport_advanced',
        'description': 'Advanced transport calculation with all optional files',
        'options': {
            'resources': {'num_machines': 1},
            'max_wallclock_seconds': 7200,
        }
    }
}

calc_node = submit(FireballCalculation, **inputs)
print(f"Submitted advanced transport calculation: PK={calc_node.pk}")
```

## Workflow Examples

### Equation of State

Using the Birch-Murnaghan workflow:

```python
from aiida import orm
from aiida.plugins import WorkflowFactory
from aiida.engine import submit

# Load the workflow
BirchMurnaghanWorkChain = WorkflowFactory('fireball.birch_murnaghan_relax')

# Set up inputs
inputs = {
    'code': orm.load_code('fireball@localhost'),
    'structure': structure,  # Your structure
    'fdata_remote': fdata_remote,
    'base_parameters': orm.Dict(dict={
        'OPTION': {'iimage': 2, 'iquench': 1, 'dt': 0.5, 'nstepf': 100},
        'OUTPUT': {'iwrtpop': 1, 'iwrtatom': 1}
    }),
    'volume_range': orm.Dict(dict={
        'min_factor': 0.85,
        'max_factor': 1.15,
        'num_points': 7
    }),
    'metadata': {
        'label': 'equation_of_state_workflow',
        'description': 'Birch-Murnaghan EOS calculation'
    }
}

# Submit workflow
wf_node = submit(BirchMurnaghanWorkChain, **inputs)
print(f"Submitted EOS workflow: PK={wf_node.pk}")
```

## Analysis Examples

### Energy Extraction

Extract and plot energies from multiple calculations:

```python
import matplotlib.pyplot as plt
from aiida import orm

# Collect calculations from a workflow or set of calculations
calc_pks = [123, 124, 125, 126, 127]  # Your calculation PKs
energies = []
volumes = []

for pk in calc_pks:
    calc = orm.load_node(pk)
    if calc.is_finished_ok:
        results = calc.outputs.output_parameters.get_dict()
        energy = results.get('total_energy')
        
        # Calculate volume from structure
        structure = calc.inputs.structure
        volume = structure.get_cell_volume()
        
        if energy is not None:
            energies.append(energy)
            volumes.append(volume)

# Plot E vs V
plt.figure(figsize=(8, 6))
plt.plot(volumes, energies, 'bo-')
plt.xlabel('Volume (Ų)')
plt.ylabel('Energy (eV)')
plt.title('Energy vs Volume')
plt.grid(True)
plt.show()
```

### Transport Analysis

Analyze transport calculation results:

```python
from aiida import orm
import numpy as np

def analyze_transport_calculation(calc_pk):
    """Analyze transport calculation results."""
    calc = orm.load_node(calc_pk)
    
    if not calc.is_finished_ok:
        print(f"Calculation {calc_pk} did not finish successfully")
        return
    
    # Get retrieved files
    retrieved = calc.outputs.retrieved
    files = retrieved.list_object_names()
    
    print(f"Generated files: {files}")
    
    # Check for transport files
    transport_files = [f for f in files if f.endswith('.optional')]
    print(f"Transport files: {transport_files}")
    
    # Read and display transport parameters
    for tf in transport_files:
        print(f"\n--- {tf} ---")
        content = retrieved.get_object_content(tf)
        print(content[:500] + "..." if len(content) > 500 else content)
    
    # Extract key results
    if 'output_parameters' in calc.outputs:
        results = calc.outputs.output_parameters.get_dict()
        
        print("\n--- Key Results ---")
        for key, value in results.items():
            if 'transport' in key.lower() or 'transmission' in key.lower():
                print(f"{key}: {value}")

# Use the analysis function
analyze_transport_calculation(your_calc_pk)
```

### Batch Processing

Process multiple structures:

```python
from aiida import orm
from aiida.plugins import CalculationFactory
from aiida.engine import submit
import numpy as np

def submit_series_calculations(base_structure, bond_lengths, code, fdata_remote):
    """Submit a series of calculations with varying bond lengths."""
    
    FireballCalculation = CalculationFactory('fireball')
    submitted_calcs = []
    
    for i, length in enumerate(bond_lengths):
        # Modify structure
        structure = base_structure.clone()
        sites = list(structure.sites)
        
        # Assuming first two atoms form the bond to modify
        if len(sites) >= 2:
            # Move second atom to adjust bond length
            direction = np.array(sites[1].position) - np.array(sites[0].position)
            direction = direction / np.linalg.norm(direction)
            new_position = sites[0].position + direction * length
            
            structure.clear_sites()
            structure.append_atom(position=sites[0].position, symbols=sites[0].kind_name)
            structure.append_atom(position=new_position, symbols=sites[1].kind_name)
            
            # Add remaining atoms
            for site in sites[2:]:
                structure.append_atom(position=site.position, symbols=site.kind_name)
        
        structure.store()
        
        # Set up calculation
        parameters = orm.Dict(dict={
            'OPTION': {'iimage': 1, 'iquench': 0, 'dt': 0.5, 'nstepf': 1},
            'OUTPUT': {'iwrtpop': 1, 'iwrtatom': 1}
        })
        
        kpoints = orm.KpointsData()
        kpoints.set_kpoints_mesh([1, 1, 1])
        kpoints.store()
        
        inputs = {
            'code': code,
            'structure': structure,
            'parameters': parameters,
            'kpoints': kpoints,
            'fdata_remote': fdata_remote,
            'metadata': {
                'label': f'bond_scan_{length:.2f}',
                'description': f'Bond length scan at {length:.2f} Å',
                'options': {
                    'resources': {'num_machines': 1},
                    'max_wallclock_seconds': 1800,
                }
            }
        }
        
        calc_node = submit(FireballCalculation, **inputs)
        submitted_calcs.append((length, calc_node))
        print(f"Submitted calculation for bond length {length:.2f} Å: PK={calc_node.pk}")
    
    return submitted_calcs

# Example usage
bond_lengths = np.arange(1.0, 2.5, 0.1)  # Å
code = orm.load_code('fireball@localhost')
# ... set up base_structure and fdata_remote ...

calculations = submit_series_calculations(base_structure, bond_lengths, code, fdata_remote)
```

## Utility Scripts

### Setup Helper

```{literalinclude} ../../../examples/setup_fdata.py
:language: python
:caption: Fdata setup helper
```

### Results Collector

```python
#!/usr/bin/env python
"""Collect results from multiple Fireball calculations."""

from aiida import orm
import pandas as pd
import argparse

def collect_results(calc_pks, output_file=None):
    """Collect results from a list of calculation PKs."""
    
    results_data = []
    
    for pk in calc_pks:
        try:
            calc = orm.load_node(pk)
            
            if not calc.is_finished_ok:
                print(f"Warning: Calculation {pk} did not finish successfully")
                continue
            
            # Basic information
            row = {
                'pk': pk,
                'label': calc.label or '',
                'description': calc.description or '',
                'creation_time': calc.ctime.isoformat(),
            }
            
            # Structure information
            if 'structure' in calc.inputs:
                structure = calc.inputs.structure
                row['formula'] = structure.get_formula()
                row['num_atoms'] = len(structure.sites)
                row['volume'] = structure.get_cell_volume()
            
            # Results
            if 'output_parameters' in calc.outputs:
                output_params = calc.outputs.output_parameters.get_dict()
                row.update(output_params)
            
            results_data.append(row)
            
        except Exception as e:
            print(f"Error processing calculation {pk}: {e}")
            continue
    
    # Create DataFrame
    df = pd.DataFrame(results_data)
    
    if output_file:
        df.to_csv(output_file, index=False)
        print(f"Results saved to {output_file}")
    
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Collect Fireball calculation results')
    parser.add_argument('pks', nargs='+', type=int, help='Calculation PKs')
    parser.add_argument('-o', '--output', help='Output CSV file')
    
    args = parser.parse_args()
    
    df = collect_results(args.pks, args.output)
    print(df)
```

## Interactive Examples

### Jupyter Notebook Workflow

```python
# Cell 1: Setup
from aiida import orm, load_profile
load_profile()

from aiida.plugins import CalculationFactory, DataFactory
from aiida.engine import submit
import matplotlib.pyplot as plt
import numpy as np

print("AiiDA profile loaded successfully")

# Cell 2: Create and visualize structure
StructureData = DataFactory('structure')

# Create H2 molecule
structure = StructureData()
structure.set_cell([[10, 0, 0], [0, 10, 0], [0, 0, 10]])
structure.append_atom(position=[0, 0, 0], symbols='H')
structure.append_atom(position=[0.74, 0, 0], symbols='H')
structure.store()

# Visualize (if you have visualization tools)
print(f"Created H2 molecule: PK={structure.pk}")
print(f"Formula: {structure.get_formula()}")

# Cell 3: Submit calculation
# ... calculation setup and submission ...

# Cell 4: Monitor and analyze
# ... results analysis and plotting ...
```

For more examples and advanced usage patterns, see the [GitHub repository](https://github.com/ValkScripter/aiida-fireball) examples directory.
