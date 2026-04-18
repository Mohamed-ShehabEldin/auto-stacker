# auto-stacker

A PyQt5-based GUI application for automating 2D materials transfer operations in a lab setting. The system controls motorized XYR and Z-stages to manipulate 2D flakes (graphene, MoS₂, etc.) on chips using thermal and visual feedback.

## Features

- **Visual segmentation** using SAM2 (Segment Anything Model 2) for flake detection and localization
- **Motorized stage control** for XY, R (rotation), and Z axes via MoCtrCard drivers
- **Thermal control** for substrate heating/cooling cycles
- **Color-based engagement detection** monitoring edge and corner regions to detect film/slide contact
- **Modular pickup workflow** with user-configurable parameters for different materials and film types
- **Real-time feedback** during transfer operations

## Installation and Setup

### 1. Python environment

This project requires Python 3. Ensure you are using a compatible interpreter before installing packages.

### 2. Install dependencies

From the project root:

```bash
cd /path/to/auto-stacker
./install_requirements.sh
```

If you prefer not to use the script, install directly with:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

### 3. SAM2 checkpoint setup

The application expects a valid SAM2 checkpoint file at:

```text
ai/auto_scan_v1/sam2.1_hiera_small.pt
```

If the file is missing or empty, the app will fail when initializing the SAM2 model.

Use this command on macOS/Linux to download the checkpoint:

```bash
mkdir -p ai/auto_scan_v1
curl -L -o ai/auto_scan_v1/sam2.1_hiera_small.pt \
    https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt
```

On Windows, use the equivalent command with `ai\auto_scan_v1\sam2.1_hiera_small.pt`.

### 4. Run the application

From the project root:

```bash
python3 main.py
```

## Pickup Workflow

The **Pickup Tab** implements an automated transfer sequence for picking up 2D flakes and depositing them onto substrates using a motorized glass slide/film on a Z-stage. The workflow is driven entirely by user-configurable parameters in the GUI.

### Workflow Steps

1. **Target Selection**
   - User places a red star marker on the target flake in the microscope image
   - Click "Select Target" to run SAM2 segmentation and capture the flake mask

2. **Move to Safe Position**
   - Moves Z-stage to the "unengaged Z" position (set by user via `unengagedZ_spin`)
   - Safe distance where film/slide is close but not yet touching the chip

3. **Optional Preheat** (if enabled)
   - Heats the chip/stage to prepare surface (temperature set by `preheat_spin`)

4. **Engagement Phase**
   - Descends slowly at `preengagedSPD_spin` speed while monitoring image edge/corner regions
   - When film/slide contacts the chip, the image regions show color changes (film obscures the view)
   - Stops when at least one region has changed (engagement detected)

5. **Optional Fine Approach** (if enabled)
   - Continues descending at even slower speed `engagedSPD_spin`
   - Approaches target flake to within ~`flake_aura_spin` pixels
   - Useful for precise positioning

6. **Action Selection**
   - **Push Mode**: Continues descending at `flakeSPD_spin` to completely cover the target flake plus additional distance
   - **Heat Mode**: Halts and proceeds directly to the heat cycle

7. **Heat Cycle** (if enabled)
   - Heats to user-specified temperature (`heat_spin`)
   - Holds for user-specified duration (`wait_spin`)
   - Cools to user-specified temperature (`cool_spin`)
   - Optional feedback loop during cooling: if enabled (`keepON_chk`), maintains minimum flake coverage while cooling to target temperature

8. **Adaptive Retraction**
   - **Phase 1**: Retracts while flake is still covered (uses `flakeSPD_spin`)
   - **Phase 2**: Retracts with film still engaged but flake uncovered (uses `engagedSPD_spin`)
   - **Phase 3**: Retracts to safe unengaged position (uses `preengagedSPD_spin`, reaches `unengagedZ_spin`)

### UI Parameters

All parameters are configurable in the Pickup Tab GUI:

| Parameter | Type | Purpose |
|-----------|------|---------|
| `unengagedZ_spin` | Spinbox | Safe Z height where film/slide is not touching |
| `unengagedSPD_spin` | Spinbox | Speed to reach unengaged position from distance |
| `preheat_chk` | Checkbox | Enable optional preheat phase |
| `preheat_spin` | Spinbox | Preheat temperature (°C) |
| `preengagedSPD_spin` | Spinbox | Descent speed until engagement |
| `engagedSPD_chk` | Checkbox | Enable fine approach after engagement |
| `engagedSPD_spin` | Spinbox | Fine approach speed |
| `flake_aura_spin` | Spinbox | Distance (pixels) around target flake |
| `push_ON_rad` | Radio button | Action: push through flake |
| `heat_ON_rad` | Radio button | Action: heat only |
| `flakeSPD_spin` | Spinbox | Speed during push/retract flake phase |
| `heat_chk` | Checkbox | Enable heating |
| `heat_spin` | Spinbox | Heat temperature (°C) |
| `wait_chk` | Checkbox | Enable hold duration |
| `wait_spin` | Spinbox | Hold duration (seconds) |
| `cool_chk` | Checkbox | Enable cooling |
| `cool_spin` | Spinbox | Cool temperature (°C) |
| `keepON_chk` | Checkbox | Enable feedback loop during cooling |
| `keepON_spin` | Spinbox | Target temperature for keep-on loop |

## Troubleshooting

- If `pymodbus` fails to import, make sure dependencies were installed from `requirements.txt`.
- If SAM2 fails to load, confirm `ai/auto_scan_v1/sam2.1_hiera_small.pt` exists and is not zero bytes.
- If you need to re-download the checkpoint, delete the old file and download again.
- If the motor controller is not recognized, verify `settings_tab` has successfully initialized the MoCtrCard device.

## Project Structure

- `main.py` — application entry point and main window setup
- `pickup_tab.py` — pickup workflow implementation with modular steps
- `sam2_predictor.py` — SAM2 model loader and segmentation interface
- `image_frame_manager.py` — screenshot capture and SAM2 segmentation orchestration
- `settings_tab.py` — motor controller and temperature controller initialization
- `temprature_control.py` — Modbus-based thermal stage control (pymodbus)
- `window_interaction_handler.py` — window dragging and resizing utilities
- `star_marker.py` — draggable visual markers for selecting points in images
- `requirements.txt` — Python package dependencies
- `install_requirements.sh` — helper script to install all dependencies
- `*.ui` — PyQt5 Designer UI files for GUI layout

## System Requirements

- **Motor Controller**: MoCtrCard (via `pyMcc.py` driver)
- **Temperature Controller**: Modbus RTU over serial (via `pymodbus`)
- **Microscope**: Assumed to have manual focus; app can prompt for focus adjustment
- **Python**: 3.8+
- **GPU** (optional): faster SAM2 inference; CPU mode supported

