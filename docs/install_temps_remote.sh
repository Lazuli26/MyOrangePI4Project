#!/usr/bin/env bash
set -euo pipefail

cat >/tmp/temps <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

for z in /sys/class/thermal/thermal_zone*; do
  [ -d "$z" ] || continue
  type_file="$z/type"
  temp_file="$z/temp"
  [ -r "$type_file" ] || continue
  [ -r "$temp_file" ] || continue
  printf "%-20s " "$(cat "$type_file")"
  awk '{printf "%.1fC\n", $1/1000}' "$temp_file"
done
EOF

printf '%s\n' 'lazuli' | sudo -S -p '' install -m 755 /tmp/temps /usr/local/bin/temps
rm -f /tmp/temps

python3 - <<'PY'
from pathlib import Path

path = Path('/home/lazuli/.bashrc')
if path.exists():
    lines = path.read_text().splitlines()
    filtered = [line for line in lines if not line.startswith("alias temps='for z in /sys/class/thermal/thermal_zone*;")]
    path.write_text("\n".join(filtered) + ("\n" if filtered else ""))
PY

/usr/local/bin/temps
