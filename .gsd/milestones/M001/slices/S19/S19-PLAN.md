# S19: Foundation

**Goal:** numpy unblock, camera config schema, camera.db schema, and config-driven zero-import guard — camera.enabled=false means zero camera code runs.
**Demo:** Application starts with camera.enabled=false and no cv2/torch imports occur; camera.enabled=true reads camera config fields.

## Must-Haves


## Tasks


## Files Likely Touched

- `requirements.txt`
- `config/config.yaml`
- `src/services/database/schemas.py`
- `src/core/lifecycle.py`
