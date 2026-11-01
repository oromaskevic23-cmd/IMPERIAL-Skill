"""Test against actual pinned IMPERIAL-Plugins source, not a mock."""
from pathlib import Path
from imperial_skill.manifest import read_json_strict
from imperial_skill.bridge import to_plugins_manifest
from imperial_plugins.core import validate_manifest

path=Path(__file__).resolve().parents[1]/"examples"/"skills"
count=0
for item in sorted(path.glob("*.json")):
    raw=read_json_strict(item.read_bytes())
    converted=to_plugins_manifest(raw)
    actual=validate_manifest(converted)
    assert actual==converted,"INCOMPATIBLE_IMPERIAL_PLUGIN_CONTRACT"
    assert set(converted["capabilities"]) <= {"read:public","simulate:task","route:internal"}
    count+=1
assert count==4
print("REAL_PINNED_PLUGIN_CONTRACT_PASS",
      "manifest_count",count,"production_execution_authorized",False,
      "connected_production_runtime",False)
