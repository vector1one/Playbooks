#!/bin/sh
# CGI: get_config.sh
# Returns the active tool/SIEM selection as JSON, driven by SIEM_TOOL_1..5 env vars.
# Defaults: sysmon, osquery, velociraptor, elastic, elastic_detection_rules

echo "Content-Type: application/json"
echo "Access-Control-Allow-Origin: *"
echo ""

T1="${SIEM_TOOL_1:-sysmon}"
T2="${SIEM_TOOL_2:-osquery}"
T3="${SIEM_TOOL_3:-velociraptor}"
T4="${SIEM_TOOL_4:-elastic}"
T5="${SIEM_TOOL_5:-elastic_detection_rules}"

printf '{"tools":["%s","%s","%s","%s","%s"]}' "$T1" "$T2" "$T3" "$T4" "$T5"
