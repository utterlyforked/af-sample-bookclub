# Spec Inconsistencies — Must Fix Before Re-run

Identified by automated review. All specs need to be regenerated once these are resolved.
Delete this file once the re-run is complete and specs have been verified.

---

## BLOCKER 1 — Tool status enum is different in foundation vs FEAT-01

The foundation spec and FEAT-01 define incompatible status values for the `Tool` entity.

**Foundation defines:**
- `Draft`, `Published`, `Borrowed`, `Unavailable`

**FEAT-01 uses:**
- `Available`, `Currently Borrowed`, `Temporarily Unavailable`

**Impact:** FEAT-02 (availability check on request), FEAT-04 (tracking active borrows), FEAT-05 (activity events) all reference tool status. They can't be consistent when the source of truth is split.

**Fix needed:** Foundation spec must define the canonical enum. Feature specs must use it verbatim.

---

## BLOCKER 2 — `Transaction` entity referenced in FEAT-03 and FEAT-04 does not exist

FEAT-03 and FEAT-04 use the entity name `Transaction` (e.g. `Rating.transaction_id`, "transaction status"). The foundation spec has no `Transaction` entity — the equivalent is `BorrowRequest`.

**Impact:** FEAT-03 `Rating` data model is unimplementable as written. FEAT-04 status machine references a non-existent entity.

**Fix needed:** FEAT-03 and FEAT-04 must be regenerated using `BorrowRequest` (the foundation name) throughout. The new engineering-spec prompt now enforces this.

---

## BLOCKER 3 — BorrowRequest status machine is inconsistent across three specs

Three specs define incompatible status progressions for the same entity:

| Spec | Status values |
|------|--------------|
| Foundation | `Pending → Approved → Declined → Cancelled → Withdrawn → PickedUp → Returned → Completed` |
| FEAT-02 | Same as foundation plus `Withdrawn` (already present above) |
| FEAT-04 | `Active → PendingReturnConfirmation → Completed → Cancelled` |

**Impact:** Return confirmation flow (FEAT-04), rating windows (FEAT-03), and activity events (FEAT-05) all depend on specific status values to trigger behaviour. With three different machines, none of them will work together.

**Fix needed:** Foundation spec defines the canonical status machine. FEAT-04 must be regenerated using foundation values — `Active` → `Approved`, `PendingReturnConfirmation` → `Returned`.

---

## BLOCKER 4 — Auto-confirm timing contradicts itself within FEAT-04

FEAT-04 contains two different values for the auto-confirmation window:
- Business rule #10: **"14 days after due_date"**
- Endpoint description: **"7-day auto-confirm"**

**Impact:** The background job, ReturnConfirmation entity, and notification schedule all depend on this number. Whichever is wrong will cause overdue borrows to be mishandled.

**Fix needed:** Confirm the correct value with the product spec (check `docs/03-refinement/FEAT-04-*/updated-v1.*.md`) and ensure FEAT-04 spec uses it consistently.

---

## BLOCKER 5 — FEAT-05 uses integer PKs; all other specs use UUID

FEAT-05 defines the `Following` table with an `integer` auto-increment PK. Every other entity in the system uses `UUID`.

**Impact:** Inconsistent PK types across the schema will require special-casing in the ORM and make joins brittle.

**Fix needed:** FEAT-05 must be regenerated with UUID PKs to match the rest of the system.

---

## HIGH — Rating window timing is inconsistent across foundation, FEAT-03, FEAT-04

Three specs describe the rating window differently:

| Spec | Rating window definition |
|------|------------------------|
| Foundation | `rating_window_closes_at = confirmed_at + 7 days` |
| FEAT-03 | "Exactly 168 hours (7 days) after `confirmed_at`, regardless of timezone" |
| FEAT-04 | Different confirmed_at definition (auto-confirm at 7 days vs 14 days — see BLOCKER 4) |

The values are numerically equivalent (7 days = 168 hours) but FEAT-03's "regardless of timezone" language conflicts with the foundation's DST-aware timestamp handling. Once BLOCKER 4 is resolved, this should align — but verify.

---

## HIGH — `deleted_at` soft-delete field referenced but not in schema (FEAT-03)

FEAT-03 describes soft-deleting user profiles ("set `deleted_at`, never actually DELETE") but the `UserProfile` schema in FEAT-03 does not include a `deleted_at` field.

**Impact:** The deletion query `WHERE deleted_at IS NULL` will fail with a column-not-found error.

**Fix needed:** Either add `deleted_at` to the UserProfile data model, or remove the soft-delete references and define the actual deletion behaviour.

---

## MEDIUM — Tool category enum has two definitions

The foundation spec defines 6 categories in seed data:
`Power Tools, Hand Tools, Gardening, Ladders & Access, Automotive, Specialty Equipment`

The foundation spec's Tool entity description lists 8 values:
`Power Tools, Hand Tools, Lawn & Garden, Ladders & Scaffolding, Plumbing, Electrical, Automotive, Other`

These differ in names (`Gardening` vs `Lawn & Garden`, `Ladders & Access` vs `Ladders & Scaffolding`) and count (6 vs 8).

**Fix needed:** Decide the canonical list and use it in one place. Foundation spec should define it; feature specs reference it.

---

## MEDIUM — ActivityEvent creation ownership is undefined (FEAT-05)

FEAT-05 references `ActivityEvent` records being created when:
- Tool status transitions to "published"
- Borrow status transitions to "returned"

But it does not specify which component is responsible for creating these events. If FEAT-01 creates tool events and FEAT-04 creates borrow events, this is an undocumented cross-feature dependency.

**Fix needed:** Foundation spec should own `ActivityEvent` creation rules, or FEAT-05 should explicitly document the integration points.

---

## Regeneration order

Fix blockers 1–3 first (they affect the foundation spec which everything else depends on), then regenerate feature specs in this order:

1. Foundation spec (fix canonical status enums, entity names, category list)
2. FEAT-01 (tool status enum fix)
3. FEAT-02 (verify BorrowRequest status references)
4. FEAT-03 (Transaction → BorrowRequest, add deleted_at, fix rating window)
5. FEAT-04 (Transaction → BorrowRequest, fix status machine, resolve auto-confirm timing)
6. FEAT-05 (UUID PKs, ActivityEvent ownership, fix status references)
