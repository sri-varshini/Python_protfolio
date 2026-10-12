# Python Portfolio

## Weather CLI

A small command-line app that looks up a city with Open-Meteo's free geocoding
and forecast APIs, then prints its current weather. No API key is required.

### Install

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e .
```

This installs the `weather` command in the active environment. The editable
install is convenient while developing; use `py -m pip install .` for a regular
installation from the project directory.

### Usage

```powershell
weather London
weather "New York" --unit fahrenheit
```

Temperature defaults to Celsius. Fahrenheit mode also displays wind speed in
miles per hour. The app needs an internet connection to reach Open-Meteo.
You can also run it without installing the command with `py weather_cli.py London`.

### Tests

The unit tests mock the API, so they run without a network connection:

```powershell
py -m unittest discover -s tests -v
```