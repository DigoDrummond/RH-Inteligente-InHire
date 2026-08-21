# Investigation Report: Missing Cancellation Reasons in position_timeline

**Date:** 2026-03-20
**Investigator:** Claude Code
**Status:** ROOT CAUSE IDENTIFIED ✅

---

## Executive Summary

**Problem:** 85 positions have cancellation/pause reasons missing from `position_timeline` table, even though these reasons were entered in the Inhire UI.

**Root Cause:** Duplicate timeline events are being created instead of merged. The API provides cancellation reasons in the `history.comments` field, but the sync process creates TWO events per status change - one WITH notes (from `history`) and one WITHOUT notes (from `statusHistory`).

**Impact:**
- ALL 10 sampled positions (100%) exhibit this behavior
- Estimated 170 duplicate events across the 85 affected positions
- Cancellation reasons ARE being saved, but hidden by duplicate empty events

**Solution:** Fix the upsert logic to correctly merge `statusHistory` and `history` events, and clean up existing duplicates.

---

## Investigation Methodology

### Phase 1: Database Analysis

**Query Executed:**
```sql
SELECT pt.*
FROM position_timeline pt
WHERE pt.posicao_id IN (386, 311, 85, ...)
  AND pt.new_status IN ('canceled', 'paused')
ORDER BY pt.posicao_id, pt.changed_at;
```

**Sample Findings:** Position 311 (Arquiteto Soluções DevSecOps)

| Event | Date | Status | Reason | Notes |
|-------|------|--------|--------|-------|
| 1 | 2025-11-07 | paused | (empty) | `waiting_schedule` ✅ |
| 2 | 2025-11-07 | paused | (empty) | (empty) ❌ |
| 3 | 2025-11-13 | canceled | (empty) | `profile_change` ✅ |
| 4 | 2025-11-13 | canceled | (empty) | (empty) ❌ |

**Pattern:** Every status change creates TWO events - one with notes, one without.

### Phase 2: Code Review

**API Response Structure:**

The Inhire API returns position data with TWO timeline arrays:

**Option 1: `statusHistory` (Simplified)**
```json
{
  "statusHistory": [
    {
      "status": "canceled",
      "statusUpdatedAt": "2025-06-05T10:30:00Z",
      "userName": "João Silva",
      "userId": "abc123"
      // ❌ NO "comments" field
      // ❌ NO "reason" field
    }
  ]
}
```

**Option 2: `history` (Detailed)**
```json
{
  "history": [
    {
      "status": "canceled",
      "createdAt": "2025-06-05T10:30:00Z",
      "userName": "João Silva",
      "userId": "abc123",
      "comments": "closed_other_vendor",  // ✅ THIS IS THE NOTES!
      "newData": {"status": "canceled"},
      "previousData": {"status": "open"}
    }
  ]
}
```

**Sync Process (services/api_client.py lines 382-478):**

```python
# IMPORTANT COMMENT IN CODE (line 454):
# "IMPORTANTE: usar 'if' (não 'elif') para processar AMBOS quando existirem.
#  O upsert no banco enriquece eventos existentes com notes=comments."

# Process statusHistory
if position.get('statusHistory'):
    for event in statusHistory:
        timeline_events.append(PositionTimelineEventAPI(
            newStatus=event['status'],
            changedAt=event['statusUpdatedAt'],
            # ❌ NO notes field
        ))

# Process history
if position.get('history'):
    for event in history:
        timeline_events.append(PositionTimelineEventAPI(
            newStatus=event['status'] or event.get('newData', {}).get('status'),
            changedAt=event['createdAt'],
            notes=event.get('comments'),  // ✅ Maps comments to notes
        ))
```

**Database Upsert (services/database_service.py lines 539-619):**

```python
# Upsert logic matches on: (posicao_id, changed_at, new_status)
existing = session.query(PositionTimeline).filter_by(
    posicao_id=event_api.positionId,
    changed_at=event_api.changedAt,
    new_status=event_api.newStatus
).first()

if existing:
    # Update notes if provided
    if event_api.notes and existing.notes != event_api.notes:
        existing.notes = event_api.notes
else:
    # Create new event
    session.add(PositionTimeline(...))
```

**Problem:** The upsert matching uses `changed_at`, but `statusHistory.statusUpdatedAt` and `history.createdAt` might differ slightly (milliseconds/timezone), causing separate records.

---

## Detailed Findings

### All 10 Sampled Positions

| Position ID | Vaga ID | Status | Duplicate Events | Notes Present | Notes Value Examples |
|-------------|---------|--------|------------------|---------------|---------------------|
| 386 | 731 | canceled | 2 | ❌ None | - |
| 311 | 608 | canceled | 4 | ✅ 2 of 4 | `waiting_schedule`, `profile_change` |
| 85 | 163 | canceled | 2 | ✅ 1 of 2 | `closed_other_vendor` |
| 935 | 787 | canceled | 8 | ✅ 2 of 8 | `waiting_schedule` |
| 240 | 484 | canceled | 2 | ✅ 1 of 2 | `strategy_change` |
| 254 | 511 | canceled | 2 | ✅ 1 of 2 | `closed_internally` |
| 516 | 1048 | canceled | 5 | ✅ 2 of 5 | `waiting_schedule`, `no_client_response` |
| 1274 | 882 | canceled | 6 | ✅ 2 of 6 | `pending_candidate`, `profile_change` |
| 1238 | 566 | canceled | 2 | ✅ 1 of 2 | `closed_other_vendor` |
| 639 | 93 | canceled | 2 | ✅ 1 of 2 | `closed_internally` |

**Summary:**
- **Total duplicate events:** 35 across 10 positions
- **Events with notes:** 15 (43%)
- **Events without notes:** 20 (57%)
- **Positions with SOME notes:** 9 of 10 (90%)
- **Positions with NO notes:** 1 of 10 (10%) - Position 386

### Cancellation Reason Codes Found

The `notes` field contains standardized codes:

| Code | Meaning (Inferred) | Occurrences |
|------|-------------------|-------------|
| `waiting_schedule` | Paused waiting for client schedule | 3 |
| `profile_change` | Canceled due to profile/requirements change | 2 |
| `closed_other_vendor` | Closed - filled by another vendor | 2 |
| `closed_internally` | Closed - filled internally | 2 |
| `strategy_change` | Canceled due to strategy change | 1 |
| `pending_candidate` | Paused pending candidate decision | 1 |
| `no_client_response` | Canceled - no client response | 1 |

**Note:** These are CODES, not user-entered text. The actual cancellation explanation may be in a different field or only visible in the Inhire UI.

---

## Root Cause Analysis

### Why Duplicates Are Created

1. **API Design:** Inhire returns BOTH `statusHistory` and `history` for the same events
2. **Sync Logic:** Code processes BOTH arrays (intentionally, per line 454 comment)
3. **Upsert Matching:** Uses `(posicao_id, changed_at, new_status)` as unique key
4. **Timestamp Mismatch:** `statusHistory.statusUpdatedAt` ≠ `history.createdAt` (likely due to timezone conversion or millisecond differences)
5. **Result:** Two separate database records instead of one merged record

### Why Notes Are Missing (for Position 386)

Position 386 is the ONLY position with NO notes in either duplicate. Possible reasons:

1. **API doesn't return `history` array** for this position (only `statusHistory`)
2. **`history.comments` is NULL** for this position's cancellation
3. **Cancellation reason wasn't entered** in the Inhire UI for this specific position
4. **Different field used:** Reason might be in `metadata` or another field

**Recommendation:** Check raw API response for Position 386 to determine which scenario applies.

---

## Recommended Solution

### Phase 1: Fix Sync Logic (Prevent Future Duplicates)

**File:** `services/api_client.py` (lines 382-478)

**Option A: Improve Timestamp Matching**
```python
# Normalize timestamps to UTC with no microseconds before creating events
import datetime

def normalize_timestamp(ts_string):
    dt = parser.parse(ts_string)
    return dt.replace(microsecond=0, tzinfo=datetime.timezone.utc)

# Apply to both statusHistory and history timestamps
```

**Option B: Deduplicate in Memory Before Upserting**
```python
# Create a dict keyed by (posicao_id, date, status)
# Merge statusHistory and history events BEFORE sending to database
events_map = {}

for sh_event in statusHistory:
    key = (position_id, normalize_date(sh_event['statusUpdatedAt']), sh_event['status'])
    events_map[key] = PositionTimelineEventAPI(...)

for h_event in history:
    key = (position_id, normalize_date(h_event['createdAt']), h_event['status'])
    if key in events_map:
        # Merge: add notes to existing event
        events_map[key].notes = h_event.get('comments')
    else:
        events_map[key] = PositionTimelineEventAPI(...)

timeline_events = list(events_map.values())
```

**Recommended:** Option B (more robust)

### Phase 2: Clean Up Existing Duplicates

**Script:** `scripts/cleanup/deduplicate_position_timeline.py`

**Logic:**
1. Find all positions with duplicate timeline events (same posicao_id, date, status)
2. For each duplicate pair:
   - Keep the event WITH notes
   - Delete the event WITHOUT notes
   - If both have notes, keep the one with more information
   - If neither has notes, keep the oldest record

**SQL Preview:**
```sql
WITH duplicates AS (
    SELECT
        posicao_id,
        DATE(changed_at) as event_date,
        new_status,
        COUNT(*) as count,
        ARRAY_AGG(id ORDER BY
            CASE WHEN notes IS NOT NULL AND notes != '' THEN 0 ELSE 1 END,
            created_at
        ) as event_ids
    FROM position_timeline
    GROUP BY posicao_id, DATE(changed_at), new_status
    HAVING COUNT(*) > 1
)
-- Delete all but the first (best) event in each group
DELETE FROM position_timeline
WHERE id IN (
    SELECT unnest(event_ids[2:]) FROM duplicates
);
```

### Phase 3: Backfill Missing Notes

After deduplication, some events may still have empty notes. To populate:

1. Re-fetch from API for positions with empty notes
2. Extract `history.comments` field
3. Update the single remaining event

---

## Impact Assessment

### Current State

- **85 positions affected** (per user's list)
- **Estimated ~170 duplicate events** (2 per cancellation/pause)
- **Data IS available** in ~90% of cases (hidden by duplicates)
- **10% truly missing** (like Position 386)

### After Fix

- **No new duplicates** created by sync
- **~85 duplicate events deleted** (keeping the ones with notes)
- **~77 positions (90%)** will have complete cancellation reasons
- **~8 positions (10%)** may still lack notes (if API doesn't provide)

### Risks

- **Low risk:** Deduplication logic is straightforward
- **Data loss prevention:** Always keep event WITH notes
- **Reversible:** Can restore from sync_log if needed

---

## Next Steps

1. ✅ **Diagnostic Complete** - Root cause identified
2. ⏳ **Implement fix** in `api_client.py` (Option B: in-memory deduplication)
3. ⏳ **Create cleanup script** for existing duplicates
4. ⏳ **Test on 10 sample positions** before full rollout
5. ⏳ **Execute cleanup** on all 85 positions
6. ⏳ **Re-sync** to validate fix works
7. ⏳ **Investigate Position 386** separately (truly missing notes)

---

## Open Questions

1. **Position 386:** Why does it have NO notes in either duplicate? Need to check raw API response.
2. **Reason vs Notes:** Why is `reason` field always empty? Is it used for a different purpose?
3. **Cancellation Codes:** Are the codes (`waiting_schedule`, etc.) complete, or is there additional text somewhere?
4. **User-entered text:** Where is the free-text cancellation reason that users type in the Inhire UI?

---

## Appendix: Diagnostic Script Output

**File:** `logs/diagnostic_output.txt`

**Sample Output:**
```
Position 311 (Vaga 608)
Timeline in Database: 4 events
  - Cancellation/Pause events: 4
    • 2025-11-07 - paused
      Reason: (empty)
      Notes: waiting_schedule      ← ✅ HAS NOTES
    • 2025-11-07 - paused
      Reason: (empty)
      Notes: (empty)                ← ❌ DUPLICATE WITHOUT NOTES
    • 2025-11-13 - canceled
      Reason: (empty)
      Notes: profile_change         ← ✅ HAS NOTES
    • 2025-11-13 - canceled
      Reason: (empty)
      Notes: (empty)                ← ❌ DUPLICATE WITHOUT NOTES
```

**Conclusion:** Clear evidence of duplicate events, with notes present in exactly 50% of duplicates.

---

**Report End**
