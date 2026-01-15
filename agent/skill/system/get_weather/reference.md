# Weather API Reference

## Available Endpoints

- `/current`: Get current weather conditions
- `/forecast`: Get weather forecast for the next few days
- `/historical`: Get historical weather data

## Parameters

- `location`: City or geographic coordinates
- `units`: Metric (Celsius) or Imperial (Fahrenheit)
- `api_key`: Required for API access

## Response Format

```json
{
  "location": "City Name",
  "temperature": {
    "celsius": 22,
    "fahrenheit": 71.6
  },
  "humidity": 65,
  "wind": {
    "speed": 12,
    "direction": "NW"
  },
  "conditions": "Partly cloudy"
}
```