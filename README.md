# QCoDeS-drivers

In this folder, we have all the drivers for instruments to be used with QCoDeS.

Examples are available in this [repo](https://github.com/QCoDeS/Qcodes_contrib_drivers), and the official documentation [here](https://microsoft.github.io/Qcodes/examples/writing_drivers/Creating-Instrument-Drivers.html).

[QCoDeS 0.54.0](https://microsoft.github.io/Qcodes/changes/0.54.0.html) introduces some breaking changes. If you want to use the code that is compatible with prior version, use the [release 0.1.0](https://github.com/QCoherence/QCodes-drivers/releases/tag/v0.1.0).

## ADwin

If you want to use the ADwin, it relies on [nanoqt](https://nanoqt.neel.cnrs.fr) with the [repo](https://cowork.neel.cnrs.fr/NanoQt/nanoqt.git) hosted at Néel. To clone it while you clone this repo, you need to run

```shell
git clone --recursive-submodules ...
```

Or after the normal cloning, you should run in the repo:

```shell
git submodule update --init
```
