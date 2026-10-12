"""Fetch and display current weather for a city using Open-Meteo."""

from __future__ import annotations

import argparse
import sys
from typing import Any

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 10

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherError(Exception):
    """An expected error while looking up or retrieving weather."""


def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise WeatherError(f"Could not reach the weather service: {exc}") from exc
    except ValueError as exc:
        raise WeatherError("The weather service returned invalid JSON.") from exc

    if not isinstance(data, dict):
        raise WeatherError("The weather service returned an unexpected response.")
    if "error" in data:
        reason = data.get("reason", "request rejected")
        raise WeatherError(f"The weather service rejected the request: {reason}")
    return data


def get_weather(city: str, unit: str = "celsius") -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the matched location and its current conditions."""
    if unit not in {"celsius", "fahrenheit"}:
        raise ValueError("unit must be 'celsius' or 'fahrenheit'")

    locations = _get_json(
        GEOCODING_URL,
        {"name": city, "count": 1, "language": "en", "format": "json"},
    ).get("results")
    if not locations:
        raise WeatherError(f"No location found for {city!r}. Check the spelling and try again.")
    location = locations[0]

    weather = _get_json(
        FORECAST_URL,
        {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "is_day,precipitation,weather_code,wind_speed_10m"
            ),
            "temperature_unit": unit,
            "wind_speed_unit": "kmh" if unit == "celsius" else "mph",
            "timezone": "auto",
        },
    )
    current = weather.get("current")
    if not isinstance(current, dict):
        raise WeatherError("The weather service did not return current conditions.")
    return location, current


def format_weather(
    location: dict[str, Any], current: dict[str, Any], unit: str = "celsius"
) -> str:
    """Format location and current conditions for terminal output."""
    temperature_unit = "C" if unit == "celsius" else "F"
    speed_unit = "km/h" if unit == "celsius" else "mph"
    code = current.get("weather_code")
    condition = WEATHER_CODES.get(code, "Unknown conditions")
    city_name = location["name"]
    country = location.get("country", "")
    place = f"{city_name}, {country}" if country else city_name

    return "\n".join(
        (
            f"Weather for {place}",
            f"  Condition:       {condition}",
            f"  Temperature:     {current['temperature_2m']} {temperature_unit}",
            f"  Feels like:      {current['apparent_temperature']} {temperature_unit}",
            f"  Humidity:        {current['relative_humidity_2m']}%",
            f"  Wind:            {current['wind_speed_10m']} {speed_unit}",
            f"  Precipitation:   {current['precipitation']} mm",
            f"  Local time:      {current.get('time', 'Unknown')}",
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch current weather for a city using the free Open-Meteo API."
    )
    parser.add_argument("city", help="city name, for example London")
    parser.add_argument(
        "--unit",
        choices=("celsius", "fahrenheit"),
        default="celsius",
        help="temperature and wind units (default: celsius)",
    )
    args = parser.parse_args(argv)

    try:
        location, current = get_weather(args.city, args.unit)
    except WeatherError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (KeyError, IndexError, TypeError) as exc:
        print(f"Error: The weather service returned incomplete data ({exc}).", file=sys.stderr)
        return 1

    print(format_weather(location, current, args.unit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
