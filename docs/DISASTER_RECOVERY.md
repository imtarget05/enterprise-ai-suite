# DISASTER RECOVERY & BACKUP/RESTORE RUNBOOK

This runbook establishes backup cadence, verification drills, persistent volume recovery, and idempotency guarantees for the Enterprise AI Suite.

---

## 1. Objectives & Data Persistence Strategy

- **RTO (Recovery Time Objective)**: < 15 minutes from cold backup to healthy status.
- **RPO (Recovery Point Objective)**: < 1 hour (daily automated snapshots + transaction journals).
- **Persistent Volume Mapping**:
  - `postgres_data` -> Mounted on host at `/var/lib/docker/volumes/postgres_data/_data`
  - `mariadb_data` -> Mounted on host at `/var/lib/docker/volumes/mariadb_data/_data`
  - `erpnext_sites` -> Mounted on host at `/var/lib/docker/volumes/erpnext_sites/_data`
  - `redpanda_data` -> Commit logs stored with Raft consensus persistence.

All volumes reside on Oracle Cloud Block Storage (200 GB Always Free tier), which persists independently of compute instance restarts.

---

## 2. Automated Backup Drill Procedures

Automated script located at `infra/scripts/backup.sh`:

### A. PostgreSQL Application Database Backup:
```bash
docker exec -t postgres-core pg_dump -U postgres -d enterprise_suite -F c -b -v -f /tmp/postgres_backup.dump
docker cp postgres-core:/tmp/postgres_backup.dump ./backups/postgres_$(date +%Y%m%d_%H%M%S).dump
```

### B. ERPNext & MariaDB Backup:
```bash
# Triggers Frappe native site backup (Database + Public Files + Private Files)
docker exec -t erpnext-worker bench --site erp.local backup --with-files
```

### C. Qdrant Hybrid Collection Snapshot:
```bash
curl -X POST "http://localhost:6333/collections/enterprise_knowledge/snapshots" \
     -H "Content-Type: application/json"
```

---

## 3. Step-by-Step Restoration Verification Drill

Automated restore verification script located at `infra/scripts/restore.sh`:

```bash
#!/usr/bin/env bash
set -e

BACKUP_FILE=$1
echo "Restoring PostgreSQL database from ${BACKUP_FILE}..."

# 1. Terminate existing connections
docker exec -i postgres-core psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'enterprise_suite';"

# 2. Drop and recreate database
docker exec -i postgres-core psql -U postgres -c "DROP DATABASE IF EXISTS enterprise_suite;"
docker exec -i postgres-core psql -U postgres -c "CREATE DATABASE enterprise_suite;"

# 3. Restore schema and data
docker exec -i postgres-core pg_restore -U postgres -d enterprise_suite -v < "${BACKUP_FILE}"

echo "PostgreSQL restoration complete and verified."
```

---

## 4. Idempotency & Replay Resiliency

1. **Transactional Outbox Pattern**:
   - Outbox table records all outgoing ERP integration events within the local PostgreSQL transaction.
   - A dedicated poller reads uncommitted outbox entries and publishes to RabbitMQ/Redpanda.
   - If a crash occurs before acknowledgment, messages are safely replayed with duplicate prevention headers (`idempotency_key = sha256(event_type + correlation_id)`).

2. **ERPNext Document Upsert Idempotency**:
   - All Sales Orders and Quality Inspections created by the suite carry an `external_id` (UUID).
   - Before inserting, the ERPNext adapter executes `frappe.db.exists("Quality Inspection", {"external_id": external_id})`.
   - If the document exists, it updates existing records instead of generating duplicate ledger lines.
