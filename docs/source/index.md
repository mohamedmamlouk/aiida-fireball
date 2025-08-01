# AiiDA Fireball Documentation

Welcome to the documentation for the **AiiDA Fireball Plugin** - a comprehensive integration of the Fireball semi-empirical DFT code with the AiiDA computational workflow management platform.

```{image} https://img.shields.io/badge/python-3.8+-blue.svg
:alt: Python version
:target: https://pypi.org/project/aiida-fireball
```

```{image} https://img.shields.io/badge/AiiDA-2.0+-blue.svg
:alt: AiiDA version
:target: https://aiida.net
```

```{image} https://img.shields.io/github/license/mohamedmamlouk/aiida-fireball
:alt: License
:target: https://github.com/mohamedmamlouk/aiida-fireball/blob/main/LICENSE
```

## What is AiiDA Fireball?

AiiDA Fireball is a plugin that enables seamless execution and management of Fireball calculations within the AiiDA ecosystem. It provides:

- **Full Fireball Integration**: Complete support for Fireball semi-empirical DFT calculations
- **Advanced Transport Calculations**: State-of-the-art transport property calculations with flexible optional files
- **Workflow Automation**: Automated equation of state calculations and parameter optimization
- **Provenance Tracking**: Full data provenance and workflow reproducibility
- **High-Throughput Capabilities**: Designed for large-scale computational studies

## Key Features

::::{grid} 2
:gutter: 3

:::{grid-item-card} 🔬 Fireball Calculations
:link: user_guide/first_calculation
:link-type: doc

Complete support for Fireball semi-empirical DFT calculations with automatic input generation and output parsing.
:::

:::{grid-item-card} 🚀 Transport Properties  
:link: user_guide/transport_tutorial
:link-type: doc

Advanced transport calculations with support for interaction, eta, trans, and bias optional files.
:::

:::{grid-item-card} 📊 Workflows
:link: user_guide/workflows
:link-type: doc

Automated Birch-Murnaghan equation of state calculations and bulk property extraction.
:::

:::{grid-item-card} 🔧 AiiDA Integration
:link: reference/api
:link-type: doc

Full compatibility with AiiDA 2.0+ ecosystem including provenance tracking and data management.
:::

::::

## Quick Start

Get started with AiiDA Fireball in just a few steps:

1. **Install the plugin**: `pip install aiida-fireball`
2. **Set up your code**: Configure Fireball executable in AiiDA
3. **Run your first calculation**: Follow our {doc}`user_guide/first_calculation`

## Documentation Contents

```{toctree}
:maxdepth: 2
:caption: User Guide

user_guide/installation
user_guide/first_calculation
user_guide/transport_tutorial
user_guide/workflows
```

```{toctree}
:maxdepth: 2
:caption: Examples

examples/index
```

```{toctree}
:maxdepth: 2
:caption: Reference

reference/index
```

## Community and Support

- **GitHub Repository**: [ValkScripter/aiida-fireball](https://github.com/ValkScripter/aiida-fireball)
- **Issues and Bug Reports**: [GitHub Issues](https://github.com/ValkScripter/aiida-fireball/issues)
- **AiiDA Community**: [AiiDA Discourse](https://aiida.discourse.group)
- **Documentation**: [ReadTheDocs](https://aiida-fireball.readthedocs.io)

## Citation

If you use this plugin in your research, please cite:

```bibtex
@software{aiida_fireball,
  title = {AiiDA Fireball Plugin},
  author = {ValkScripter and Mohamed Mamlouk},
  url = {https://github.com/ValkScripter/aiida-fireball},
  year = {2024}
}
```

Also consider citing AiiDA and Fireball:

- [AiiDA](https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/citing.html)
- [Fireball DFT](http://fireball-dft.org)

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/ValkScripter/aiida-fireball/blob/main/LICENSE) file for details.

## Citation

If you use AiiDA Fireball in your research, please cite:

```bibtex
@misc{aiida_fireball,
  title={AiiDA Fireball Plugin: High-Throughput Semi-Empirical DFT with Transport Calculations},
  author={ValkScripter and mohamedmamlouk},
  year={2025},
  url={https://github.com/mohamedmamlouk/aiida-fireball},
  note={Version 1.0.0}
}
```

## Support and Community

- **Documentation**: You're reading it! 📖
- **Issues**: [GitHub Issues](https://github.com/mohamedmamlouk/aiida-fireball/issues) 🐛
- **Discussions**: [GitHub Discussions](https://github.com/mohamedmamlouk/aiida-fireball/discussions) 💬
- **AiiDA Community**: [AiiDA Discourse](https://aiida.discourse.group/) 🌐

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/mohamedmamlouk/aiida-fireball/blob/main/LICENSE) file for details.

## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
