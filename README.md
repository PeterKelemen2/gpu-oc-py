# GPU OC Python Controller

A small user-space Python application that applies NVIDIA GPU overclock settings and monitors GPU health.

The app uses NVIDIA NVML to lock GPU clocks, apply a voltage/frequency offset, and optionally enforce a power limit. It also monitors the GPU for driver failure and can reload the NVIDIA kernel module if a crash is detected.

## Features

- Apply GPU overclock settings from `config.toml`
- Monitor GPU temperature and driver health
- Recover from NVIDIA driver crashes by reloading the kernel module
- Use the Linux watchdog to reboot the system if the process stops responding

## Requirements

- Python 3.12+
- NVIDIA driver with NVML support
- Root permissions to access `/dev/watchdog` and interact with NVIDIA driver modules

Dependencies are listed in `requirements.txt`.

## Setup

The easiest way to install is using the provided install script:

```bash
sudo scripts/install.sh
```

This script will:
- Verify NVIDIA drivers are installed
- Check for hardware watchdog support
- Create a Python virtual environment at `/opt/gpu-oc/.venv`
- Install dependencies
- Copy `config.toml.example` to `config.toml` if it doesn't exist
- Register the systemd service

**Then configure your GPU settings:**

```bash
sudo nano /opt/gpu-oc/config/config.toml
```

**Start the service:**

```bash
sudo systemctl start gpu-oc
```

**Check status:**

```bash
sudo systemctl status gpu-oc
sudo journalctl -u gpu-oc -f  # Live logs
```

### Manual Setup (Advanced)

If you prefer to set up manually:

1. Install Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

2. Create a configuration file:

```bash
cp config/config.toml.example config/config.toml
```

3. Edit `config/config.toml` and set values for your GPU.

4. (Optional) Install the app locally:

```bash
python3 -m pip install .
```

For development:

```bash
python3 -m pip install -e .
```

## Configuration

The `config.toml` file must include a `[profile]` section with:

- `gpu_index`: GPU index to control (0 = first GPU)
- `core_offset_mhz`: Core clock voltage/frequency offset in MHz
- `power_limit_watt`: Power limit in Watts (optional)
- `max_core_clock_mhz`: Maximum locked core clock in MHz
- `display_manager`: Optional display manager service name (e.g. `gdm`, `sddm`, `lightdm`)

Example:

```toml
[profile]
gpu_index = 0
core_offset_mhz = 170
power_limit_watt = 260
max_core_clock_mhz = 2000
display_manager = "plasmalogin"
```

If `display_manager` is configured, the app will attempt to stop and restart that service around NVIDIA driver reloads.

## Running

### As a systemd service (recommended)

After installation with `sudo scripts/install.sh`, the service is automatically enabled and ready to start:

```bash
sudo systemctl start gpu-oc
sudo systemctl enable gpu-oc    # Enable autostart on boot
```

Monitor the service:

```bash
sudo systemctl status gpu-oc
sudo journalctl -u gpu-oc -f    # Follow logs in real-time
```

Stop the service:

```bash
sudo systemctl stop gpu-oc
```

### Running manually

From the project directory:

```bash
python3 -m gpu_oc.app
```

The app will:
- Load the OC profile from `GPU_OC_CONFIG` (default: `config/config.toml`)
- Apply GPU overclock settings
- Start monitoring GPU health
- Arm the watchdog if `/dev/watchdog` exists

Press `Ctrl+C` to exit; the app will disarm the watchdog and reset the GPU to safe defaults.

### Uninstalling

To cleanly remove the service and all installed files:

```bash
sudo scripts/uninstall.sh
```

This will stop the service, disable autostart, and remove `/opt/gpu-oc`.

## Notes

- The GPU OC app is a user-space application, not a kernel module.
- The Linux watchdog requires a loaded watchdog kernel module such as `softdog` or `iTCO_wdt`.
- Run as root for watchdog support and NVIDIA driver recovery.
- Installation defaults to `/opt/gpu-oc`; use `GPU_OC_CONFIG` environment variable to override config path.
- The systemd service includes restart limits to prevent restart loops if configuration is invalid.

## Troubleshooting

**Config file not found:**
- The install script automatically copies `config.toml.example` to `config.toml`
- If missing, manually copy: `cp config/config.toml.example config/config.toml`

**Service won't start:**
```bash
sudo journalctl -u gpu-oc -n 50  # View last 50 lines of logs
```

**Service keeps restarting:**
- Check your `config.toml` for validation errors
- Verify `gpu_index`, `max_core_clock_mhz`, and other settings are valid
- Service has a restart limit (3 restarts in 60 seconds) to prevent restart loops

**Cannot open `/dev/watchdog`:**
- Run as root: `sudo systemctl start gpu-oc`
- Or load a watchdog kernel module: `sudo modprobe softdog` or check BIOS for hardware watchdog

**NVIDIA driver reload fails:**
- There may be processes holding the GPU open (e.g., GUI, CUDA apps)
- Check running processes: `lsof | grep nvidia`
- Verify display manager is installed if configured in `config.toml`

**GPU clocks not being applied:**
- Verify root permissions: `sudo systemctl status gpu-oc`
- Check NVIDIA driver supports clock locking for your GPU model
- Review logs for specific errors: `sudo journalctl -u gpu-oc -f`
