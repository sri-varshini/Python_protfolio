import unittest
from unittest.mock import Mock, patch

import requests

import Weather_forecast.weather_cli as weather_cli


class WeatherCliTests(unittest.TestCase):
    def test_get_weather_geocodes_city_and_fetches_current_conditions(self):
        location = {"name": "London", "country": "United Kingdom", "latitude": 51.5, "longitude": -0.1}
        current = {
            "temperature_2m": 18.2,
            "apparent_temperature": 17.4,
            "relative_humidity_2m": 60,
            "wind_speed_10m": 12.0,
            "precipitation": 0.0,
            "weather_code": 1,
            "time": "2025-06-01T12:00",
        }
        responses = [Mock(), Mock()]
        responses[0].json.return_value = {"results": [location]}
        responses[1].json.return_value = {"current": current}

        with patch.object(weather_cli.requests, "get", side_effect=responses) as get:
            found_location, found_current = weather_cli.get_weather("London")

        self.assertEqual(found_location, location)
        self.assertEqual(found_current, current)
        self.assertEqual(get.call_count, 2)
        self.assertEqual(get.call_args.kwargs["params"]["temperature_unit"], "celsius")

    def test_fahrenheit_uses_fahrenheit_and_mph(self):
        responses = [Mock(), Mock()]
        responses[0].json.return_value = {
            "results": [{"name": "New York", "latitude": 40.7, "longitude": -74.0}]
        }
        responses[1].json.return_value = {"current": {"temperature_2m": 70}}

        with patch.object(weather_cli.requests, "get", side_effect=responses) as get:
            weather_cli.get_weather("New York", "fahrenheit")

        params = get.call_args.kwargs["params"]
        self.assertEqual(params["temperature_unit"], "fahrenheit")
        self.assertEqual(params["wind_speed_unit"], "mph")

    def test_unknown_city_raises_weather_error(self):
        response = Mock()
        response.json.return_value = {"results": None}

        with patch.object(weather_cli.requests, "get", return_value=response):
            with self.assertRaisesRegex(weather_cli.WeatherError, "No location found"):
                weather_cli.get_weather("Not a real city")

    def test_request_failure_is_reported_as_weather_error(self):
        with patch.object(
            weather_cli.requests,
            "get",
            side_effect=requests.Timeout("connection timed out"),
        ):
            with self.assertRaisesRegex(weather_cli.WeatherError, "Could not reach"):
                weather_cli.get_weather("London")

    def test_format_weather_includes_conditions_and_units(self):
        result = weather_cli.format_weather(
            {"name": "London", "country": "United Kingdom"},
            {
                "weather_code": 3,
                "temperature_2m": 18,
                "apparent_temperature": 17,
                "relative_humidity_2m": 60,
                "wind_speed_10m": 12,
                "precipitation": 0,
                "time": "2025-06-01T12:00",
            },
        )

        self.assertIn("Weather for London, United Kingdom", result)
        self.assertIn("Overcast", result)
        self.assertIn("18 C", result)
        self.assertIn("12 km/h", result)


if __name__ == "__main__":
    unittest.main()
