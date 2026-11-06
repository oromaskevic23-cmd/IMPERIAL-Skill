"""Test against actual pinned IMPERIAL-Plugins source, not a mock."""
from pathlib import Path
from imperial_skill.manifest import read_json_strict
from imperial_skill.bridge import to_plugins_manifest
from imperial_plugins.core import validate_manifest

path=Path(__file__).resolve().parents[1]/"examples"/"skills"
count=0
seen_ids=set()
for item in sorted(path.glob("*.json")):
    raw=read_json_strict(item.read_bytes())
    converted=to_plugins_manifest(raw)
    actual=validate_manifest(converted)
    assert actual==converted,"INCOMPATIBLE_IMPERIAL_PLUGIN_CONTRACT"
    assert set(converted["capabilities"]) <= {"read:public","simulate:task","route:internal"}
    assert raw["skill_id"] not in seen_ids,"DUPLICATE_SKILL_ID"
    seen_ids.add(raw["skill_id"])
    count+=1
new_ids={
    "imperial.skill.perplexity-research",
    "imperial.skill.firecrawl-extraction",
    "imperial.skill.posthog-analytics",
    "imperial.skill.playwright-e2e",
    "imperial.skill.composio-mcp-actions",
}
assert new_ids.issubset(seen_ids),"MISSING_GOVERNED_PROVIDER_SKILLS"
assert count >= 14,"UNEXPECTED_MANIFEST_REGRESSION"
print("REAL_PINNED_PLUGIN_CONTRACT_PASS",
      "manifest_count",count,"production_execution_authorized",False,
      "connected_production_runtime",False)
