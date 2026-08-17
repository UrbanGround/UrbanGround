# Controls and HTTP API

UrbanGround supports direct human control and programmatic control through the HTTP server
embedded in the desktop application. The browser edition uses its own in-page bridge; the HTTP
endpoints below apply to the macOS, Windows, and Linux builds.

## Manual controls

Click the first-person view once to capture the pointer. Press `Esc` to release it.

| Context | Input | Operation |
| --- | --- | --- |
| First person | `W` `A` `S` `D` | Walk forward, left, backward, and right |
| First person | Mouse | Turn and look |
| First person | `Shift` | Sprint while moving |
| First person | `Space` | Jump |
| Any view | `Tab` | Switch between first-person and map views |
| Any view | `C` | Show or hide the 3D pedestrian network |
| Any view | `F` | Open or close the experimental task library |

The map provides a second set of controls.

| Input | Operation |
| --- | --- |
| Left click | Select a point and request its location information |
| Left drag | Orbit the map camera |
| Right drag | Pan the map |
| `W` `A` `S` `D` or arrow keys | Pan the map |
| Mouse wheel or `+` / `-` | Zoom in or out |
| `N` | Start or clear pedestrian navigation to the selected point |
| `T` | Teleport to the selected point and return to first person |

## Server connection

The desktop application listens locally on port `8081` by default:

```text
http://127.0.0.1:8081
```

Check that the application is ready before starting an agent loop:

```bash
curl http://127.0.0.1:8081/health
```

The server enables CORS. It binds to `localhost` by default; `-host +` can expose it to other
machines on a trusted network, and `-port <number>` changes the port. Do not expose an
unauthenticated instance to the public internet.

If a build is configured with an API token, include it in each request:

```text
Authorization: Bearer <token>
```

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` or `/health` | Server status |
| `GET` | `/state` | View mode, WGS84 position, orientation, simulation state, interaction counters, and tile progress |
| `GET` | `/profile` | Simulated resident profile and current condition |
| `GET` | `/screenshot` | Current first-person or map observation |
| `GET` | `/task` | Current task, map endpoints, and dynamic closures |
| `GET` | `/tileset_source` | Active official or local 3D Tiles source and probe status |
| `POST` | `/action` | Execute one JSON action |
| `POST` | `/task/enter` | Load a task by ID and move to its start |
| `POST` | `/task/exit` | Clear the current task and its scene state |
| `POST` | `/stats/reset` | Reset cumulative interaction counters |

Mutating actions are serialized by the application: two clients cannot drive the avatar at the
same time.

## JSON responses

Except for `/screenshot`, the endpoints above return UTF-8 JSON objects. Successful operational
responses use `"ok": true` where applicable. An unsuccessful request includes an `error` message
and may also set `"ok": false`; the HTTP status code distinguishes invalid requests,
authentication failures, missing routes, unavailable runtime state, and timeouts. `/state` and
`/task` return their data directly and therefore do not add an `ok` field.

| Endpoint | Information returned |
| --- | --- |
| `/health` | `ok`, `service`, runtime `status`, and the available `endpoints` |
| `/state` | Camera mode and pose, pedestrian-network surface, simulation time and weather, pedestrian state, rain exposure, collision counters, tile-loading progress, and whether the scene is idle |
| `/profile` | `ok`, `name`, `gender`, `age`, `occupation`, `hunger`, `fatigue`, `activity`, `balance`, `income_today`, `total_income`, and `hourly_wage` |
| `/task` | `active`; an active task also provides `id`, `type`, `type_name`, labelled `end_points` with latitude and longitude, and the `restricted_zones` count |
| `/tileset_source` | `ok`, `probe_completed`, `internal_reachable`, `source`, `probe_latency_ms`, `internal_base_url`, `config_file`, `config_status`, and the `f2`, `building`, and `infrastructure` URLs in `tilesets` |
| `/action` | `ok`, a human-readable `action` result, and the complete post-action `state`; optional image requests add `image`, or `interval` and an `images` array |
| `/task/enter` | `ok`, the executed `action` result, and the loaded `task` object |
| `/task/exit` | `ok` and the executed `action` result |
| `/stats/reset` | `ok`, with an `error` message if the counters are unavailable |

The `/state` object groups the following fields:

| Information | Fields |
| --- | --- |
| View and pose | `mode`, `lat`, `lon`, `alt`, `yaw`, `pitch` |
| Pedestrian surface | `surface`, `on_sidewalk` |
| Simulation | `time`, `weather`, `weather_label` |
| Pedestrians | `pedestrians_active`, `pedestrian_count` |
| Rain and shelter | `is_raining`, `rain_intensity`, `being_rained_on`, `has_overhead_shelter` |
| Run counters | `rain_hits`, `rain_exposure_seconds`, `pedestrian_collisions`, `building_collisions`, `stats_tracked_seconds` |
| Loading and execution | `tiles_progress`, `tiles_settled`, `idle` |

A standard action response has the following form:

```json
{
  "ok": true,
  "action": "move: forward for 0.8s",
  "state": {
    "mode": "first_person",
    "lat": 22.319800,
    "lon": 114.169400,
    "alt": 12.50,
    "yaw": 135.20,
    "pitch": -5.10,
    "surface": "Footway - Nathan Road",
    "on_sidewalk": true,
    "time": "18:30:00",
    "weather": "sunny",
    "pedestrians_active": true,
    "pedestrian_count": 58,
    "tiles_progress": 99.98,
    "tiles_settled": true,
    "idle": true
  }
}
```

The example abbreviates `state`; the actual response contains every field listed above. Image
fields are base64 data URLs. `/screenshot` is the only endpoint in this interface that returns
binary JPEG or PNG data rather than JSON.

## Observations

### State

```bash
curl http://127.0.0.1:8081/state
```

The response includes `mode`, `lat`, `lon`, `alt`, `yaw`, `pitch`, `surface`, `on_sidewalk`,
`time`, `weather`, pedestrian state, collision and rain counters, `tiles_progress`,
`tiles_settled`, and `idle`.

### Screenshots

The default response is a JPEG matching the game-window dimensions:

```bash
curl -o observation.jpg http://127.0.0.1:8081/screenshot
```

Resolution, encoding, quality, and screen-space UI can be selected with query parameters:

```bash
curl -o observation.png \
  'http://127.0.0.1:8081/screenshot?width=1280&height=720&format=png'

curl -o displayed-frame.jpg \
  'http://127.0.0.1:8081/screenshot?quality=85&include_ui=1'
```

`width` and `height` are clamped to 16-4096 pixels. `quality` accepts 1-100. Omitting
`include_ui=1` uses an offscreen camera capture without panels or captions.

## Actions

Send one JSON object to `POST /action`. A reply contains the executed action label and the state
after execution.

```bash
curl -X POST http://127.0.0.1:8081/action \
  -H 'Content-Type: application/json' \
  -d '{"action":"move","dir":"forward","seconds":0.8}'
```

### First-person actions

| Action | Fields | Notes |
| --- | --- | --- |
| `move` | `dir`, `seconds` | `dir`: `forward`, `backward`, `left`, or `right` |
| `sprint` | `dir`, `seconds` | Uses the same directions as `move` |
| `look` | `yaw`, `pitch` | Degrees; positive yaw turns right and positive pitch looks up |
| `jump` | none | Requests one jump |
| `open_map` | none | Enters map mode |

`move` and `sprint` can turn and jump without splitting the motion into multiple calls. Optional
fields are `yaw_rate`, `pitch_rate`, `jump`, and `jump_at`:

```json
{
  "action": "sprint",
  "dir": "forward",
  "seconds": 1.0,
  "yaw_rate": 90,
  "jump_at": 0.3
}
```

The released Python client limits `move` and `sprint` calls to 0.05-2 seconds so observations can
be refreshed regularly.

### Map actions

| Action | Fields | Notes |
| --- | --- | --- |
| `map_orbit` | `yaw`, `pitch` | Rotates the map camera by the supplied degrees |
| `map_zoom` | `factor` | Values below 1 move closer; values above 1 move farther away |
| `map_pan` | `east`, `north` | Moves the focus point in metres |
| `map_select` | `x`, `y` | Normalized screen coordinates from 0 to 1, with `y=0` at the top |
| `identify_location` | none | Returns official location information for the selected point |
| `navigate` | none | Computes a pedestrian route to the selected point |
| `clear_route` | none | Removes the current pedestrian route |
| `map_teleport` | none | Teleports to the selected point |
| `close_map` | none | Returns to first person |

Call `map_select` before `identify_location`, `navigate`, or `map_teleport`.

### Environment actions

| Action | Fields | Notes |
| --- | --- | --- |
| `teleport` | `lat`, `lon`, `height` | WGS84 coordinate; `alt` is accepted in place of `height` |
| `show_network` / `hide_network` / `toggle_network` | none | Controls the pedestrian-network overlay |
| `where_am_i` | none | Reports the pedestrian-network surface under the avatar |
| `set_weather` | `weather` | `sunny`, `partly_cloudy`, `cloudy`, `overcast`, `rainy`, or `thunderstorm` |
| `set_time` | `hour`, `minute` | Uses a 24-hour clock |
| `set_time_scale` | `factor` | Changes the simulation clock speed |
| `enable_pedestrians` / `disable_pedestrians` | none | Starts or clears background pedestrians |
| `enter_task` | `id` | Loads a task from the package bundled with the running build |
| `exit_task` | none | Clears the active task |

The model-facing agent loop also recognizes `{"action":"terminate"}` as a signal to stop. It
is handled by the runner rather than as a scene mutation and should not be sent directly to
`POST /action`.

### Returning images with actions

Add `?image=1` to receive one post-action JPEG as a base64 data URL in the `image` field:

```bash
curl -X POST 'http://127.0.0.1:8081/action?image=1' \
  -H 'Content-Type: application/json' \
  -d '{"action":"look","yaw":30,"pitch":0}'
```

For a moving observation sequence, use `interval` and `max_frames`. The reply contains an
`images` array sampled while the action runs.

```bash
curl -X POST 'http://127.0.0.1:8081/action?interval=0.25&max_frames=12' \
  -H 'Content-Type: application/json' \
  -d '{"action":"move","dir":"forward","seconds":2}'
```

## Task loading

Task IDs always resolve inside the `task` directory bundled with the running application. Enter
and leave a selected task with the following requests:

```bash
curl -X POST http://127.0.0.1:8081/task/enter \
  -H 'Content-Type: application/json' \
  -d '{"id":"LQ-20260713-151300"}'

curl -X POST http://127.0.0.1:8081/task/exit
```

Loading a task teleports the avatar to its start and applies its map endpoint, closures, weather,
time, or pedestrian state as required. `/task/exit` clears those changes.

## Python client

The evaluation toolkit provides `AgentClient`, which wraps the HTTP interface and decodes image
payloads:

```python
from AgentEvaluation.sandbox import AgentClient

client = AgentClient("http://127.0.0.1:8081")
client.wait_until_ready(timeout=120)

state = client.get_state()
frame = client.screenshot()

client.look(yaw=25, pitch=-5)
client.move("forward", seconds=0.8)

client.open_map()
client.map_select(x=0.54, y=0.46)
client.navigate()
```

Use `client.act({...})` for an action that does not have a convenience method. The complete
evaluation runner in `AgentEvaluation/run_task.py` manages application launch, task selection,
the model loop, trajectory recording, and scoring.
