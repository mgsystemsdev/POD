#!/bin/bash
# Surfaces decisions flagged as REVIEW DUE from ~/.claude/decisions.csv
# Run manually or pipe to less: bash ~/agents/agent-services/workers/review.sh

CSV="$HOME/.claude/decisions.csv"

if [ ! -f "$CSV" ]; then
    echo "No decisions.csv found at $CSV"
    exit 0
fi

DUE=$(grep "REVIEW DUE" "$CSV" 2>/dev/null)

if [ -z "$DUE" ]; then
    echo "No decisions due for review."
    exit 0
fi

echo "========================================"
echo "  DECISIONS DUE FOR REVIEW"
echo "  $(date +%Y-%m-%d)"
echo "========================================"
echo ""

echo "$DUE" | while IFS=, read -r dt decision reasoning expected review_date status; do
    echo "  Date:     $dt"
    echo "  Decision: $decision"
    echo "  Why:      $reasoning"
    echo "  Expected: $expected"
    echo "  Review:   $review_date"
    echo "  ----------------------------------------"
done

COUNT=$(echo "$DUE" | wc -l | tr -d ' ')
echo ""
echo "$COUNT decision(s) need review."
echo "Edit: ~/.claude/decisions.csv (set status to 'reviewed' when done)"
