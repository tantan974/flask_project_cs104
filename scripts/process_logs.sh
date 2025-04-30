#!/bin/bash

# Log processing script: filter, parse, sort, and convert logs to CSV

# Default filter and sort options
FILTER_LEVEL=""
FILTER_EVENT=""
SORT_FIELD="line"
SORT_ORDER="asc"

# Parse command-line options
while getopts ":l:e:s:o:" opt; do
  case $opt in
    l) FILTER_LEVEL="$OPTARG" ;;
    e) FILTER_EVENT="$OPTARG" ;;
    s) SORT_FIELD="$OPTARG" ;;
    o) SORT_ORDER="$OPTARG" ;;
    \?) echo "Invalid option -$OPTARG" >&2; exit 1 ;;
  esac
done

shift $((OPTIND-1))

# Check for required arguments
if [ $# -lt 2 ]; then
  echo "Usage: $0 [-l level] [-e event] [-s line|event] [-o asc|desc] <logfile> <progressfile>"
  exit 1
fi

LOGFILE="$1"
PROGRESS_FILE="$2"

# Count lines correctly, even if last line has no newline
TOTAL_LINES=$(awk 'END{print NR}' "$LOGFILE")

OUTPUT_FILE="structured_data.csv"
TMP_FILE=$(mktemp)
SKIPPED_LINES=""

# Write CSV header
echo "Line ID,Timestamp,Level,Content,Event ID,Event Template" > "$TMP_FILE"

# Parse one log line, output CSV if valid, else return 1
process_line() {
  local line="$1"
  local LINE_ID="$2"
  [[ -z "$line" ]] && return 1
  if [[ ! "$line" =~ ^\[.*\]\ \[.*\]\ .* ]]; then
    return 1
  fi
  local TIMESTAMP=$(grep -oP '^\[\K[^\]]+' <<< "$line")
  local LEVEL=$(grep -oP '^\[[^]]+\]\ \[\K[^]]+' <<< "$line")
  local CONTENT=$(sed -E 's/^\[[^]]+\] \[[^]]+\] //' <<< "$line")
  local EVENT_ID="Unknown"
  local EVENT_TEMPLATE="$CONTENT"
  case "$CONTENT" in
    "jk2_init() Found child"*) EVENT_ID="E1"; EVENT_TEMPLATE="jk2_init() Found child <*> in scoreboard slot <*>";;
    "workerEnv.init() ok"*) EVENT_ID="E2"; EVENT_TEMPLATE="workerEnv.init() ok <*>";;
    "mod_jk child workerEnv in error state"*) EVENT_ID="E3"; EVENT_TEMPLATE="mod_jk child workerEnv in error state <*>";;
    "[client"*"] Directory index forbidden by rule:"*) EVENT_ID="E4"; EVENT_TEMPLATE="[client <*>] Directory index forbidden by rule: <*>";;
    "jk2_init() Can't find child"*) EVENT_ID="E5"; EVENT_TEMPLATE="jk2_init() Can't find child <*> in scoreboard";;
    "mod_jk child init"*) EVENT_ID="E6"; EVENT_TEMPLATE="mod_jk child init <*> <*>";;
  esac
  # Apply filters if set
  if [[ -n "$FILTER_LEVEL" && "${LEVEL,,}" != "${FILTER_LEVEL,,}" ]]; then return 1; fi
  if [[ -n "$FILTER_EVENT" && "$EVENT_ID" != "$FILTER_EVENT" ]]; then return 1; fi
  printf '%d,"%s","%s","%s","%s","%s"\n' \
    "$LINE_ID" "$TIMESTAMP" "$LEVEL" "$CONTENT" "$EVENT_ID" "$EVENT_TEMPLATE"
  return 0
}

LINE_ID=1
while IFS= read -r line || [[ -n "$line" ]]; do
  if output=$(process_line "$line" $LINE_ID); then
    echo "$output" >> "$TMP_FILE"
  else
    # Track skipped lines for display
    if [[ -z "$SKIPPED_LINES" ]]; then
      SKIPPED_LINES="$LINE_ID"
    else
      SKIPPED_LINES="$SKIPPED_LINES, $LINE_ID"
    fi
  fi
  # Write progress for the frontend
  echo "$LINE_ID/$TOTAL_LINES|$SKIPPED_LINES" > "$PROGRESS_FILE"
  ((LINE_ID++))
done < "$LOGFILE"

# Sort output as requested
if [[ "$SORT_FIELD" == "line" ]]; then
  head -n 1 "$TMP_FILE" > "$OUTPUT_FILE"
  if [[ "$SORT_ORDER" == "desc" ]]; then
    tail -n +2 "$TMP_FILE" | sort -t, -k1,1nr >> "$OUTPUT_FILE"
  else
    tail -n +2 "$TMP_FILE" | sort -t, -k1,1n >> "$OUTPUT_FILE"
  fi
  rm "$TMP_FILE"
else
  head -n 1 "$TMP_FILE" > "$OUTPUT_FILE"
  tail -n +2 "$TMP_FILE" | \
    sort -t, $( [[ "$SORT_ORDER" == "desc" ]] && echo "-k5,5r" || echo "-k5,5" ) -k1,1n >> "$OUTPUT_FILE"
  rm "$TMP_FILE"
fi

# Final progress update (no skipped lines needed on processing page)
echo "Processed $((LINE_ID-1)) lines. Output: $OUTPUT_FILE|" > "$PROGRESS_FILE"

# Save skipped lines for display page
SKIPPED_FILE="skipped_lines.txt"
if [[ -n "$SKIPPED_LINES" ]]; then
  echo "$SKIPPED_LINES" > "$SKIPPED_FILE"
else
  echo "" > "$SKIPPED_FILE"
fi

exit 0
