---
trigger: always_on
alwaysApply: true
---
1.使用“简体中文”回答问题
2.不要修改与任务非直接相关的代码
# Strict Refactor / Optimize / Bugfix Mode v5 (with Backup & Rollback)

```bash
# Create mode indicator file
STRICT_MODE_FILE="$HOME/.cursor/.strict_mode"
echo "active" > "$STRICT_MODE_FILE"
echo "Strict Mode (Refactor/Optimize/Bugfix) with Backup activated for this session"
```

## Core Principles

- **Single Source of Truth**: Only the new implementation remains. Old or redundant implementations must be deleted.
- **No Transitional Layers**: Do not create adapters, shims, converters, or wrappers to keep old APIs alive.
- **Direct Replacement**: Replace all old code references with the new implementation.
- **No Multi-layer Calls**: Prevent old and new logic from coexisting in call chains.
- **Functionality Freeze**: Unless explicitly permitted, existing feature sets and behavior must remain identical.
- **Optimization Scope**: Performance improvements, code simplification, and architecture refinements are allowed without altering functionality.
- **Bugfix Scope**: Fix issues in logic or correctness, but avoid unrequested feature changes.
- **Cross-System Consistency**: Backend, frontend, and database must remain synchronized. If one changes, related updates in the others must be implemented in the same change set.

## Backup & Rollback Requirements

1. **Selective Backup Before Change**

   - Backup only the files that will be modified into `./backup/{change-type}_{change-purpose}/`
   - `{change-type}` must be one of: `refactor`, `optimize`, `bugfix`
   - Preserve their original directory structure.
   - If backend, frontend, or database changes are interdependent, all relevant files must be backed up together.

2. **Change Report**

   - Save a detailed `CHANGE_REPORT.md` inside the backup directory.
   - Must include:
     - Change type: `refactor` / `optimize` / `bugfix`
     - Purpose and scope of the change
     - List of modified/removed/renamed files, classes, functions
     - Mapping of old → new implementations (if applicable)
     - Any intentional breaking changes (must be explicitly highlighted)
     - **Cross-system dependencies**: Explicitly describe backend/frontend/database updates and how they remain consistent.

3. **Rollback Script**

   - Save `rollback.sh` inside the backup directory.
   - The script must:
     - Remove the modified code files
     - Restore the backup files to their original locations
     - Confirm rollback completion

   Example rollback.sh:

   ```bash
   #!/bin/bash
   set -e
   BACKUP_DIR="./backup/{change-type}_{change-purpose}"
   echo "Rolling back project to backup: $BACKUP_DIR"
   rsync -av --delete "$BACKUP_DIR/" "./"
   echo "Rollback complete"
   ```

4. **Verification Step**

   - After changes, ensure all features still work as before.
   - For optimizations, confirm performance improvements without breaking logic.
   - For bugfixes, confirm the issue is resolved and no regressions are introduced.
   - For cross-system changes, confirm backend, frontend, and database are consistent, integrated, and functionally compatible.

## Explicit Prohibitions

- ❌ Do not leave old code for “compatibility.”
- ❌ Do not generate multiple versions of the same function.
- ❌ Do not expand scope with unnecessary abstractions or features.
- ❌ Do not silently change functionality.
- ❌ Do not modify backend without syncing required frontend/database changes.
- ❌ Do not update frontend or database without syncing necessary backend logic.

## Output Requirements

- Final updated code (no old code left in use).
- A `backup/{change-type}_{change-purpose}/` folder containing:
  - Only the modified files (pre-change)
  - `CHANGE_REPORT.md` (full explanation)
  - `rollback.sh` (rollback script)
- Ensure functional equivalence between old and new versions, unless explicitly directed otherwise.
- For backend, frontend, or database changes, ensure all dependent updates are included and documented together.

---

To deactivate Strict Mode:

```bash
rm -f "$STRICT_MODE_FILE"
echo "Strict Mode deactivated"
```
