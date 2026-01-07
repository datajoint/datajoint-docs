# Backup and Restore

Protect your data with proper backup strategies.

> **Tip:** [DataJoint.com](https://datajoint.com) provides automatic backups with point-in-time recovery as part of the managed service.

## Overview

A complete DataJoint backup includes:
1. **Database** — Table structures and relational data
2. **Object storage** — Large objects stored externally

## Database Backup

### Using mysqldump

```bash
# Backup single schema
mysqldump -h host -u user -p database_name > backup.sql

# Backup multiple schemas
mysqldump -h host -u user -p --databases schema1 schema2 > backup.sql

# Backup all schemas
mysqldump -h host -u user -p --all-databases > backup.sql
```

### Include Routines and Triggers

```bash
mysqldump -h host -u user -p \
    --routines \
    --triggers \
    database_name > backup.sql
```

### Compressed Backup

```bash
mysqldump -h host -u user -p database_name | gzip > backup.sql.gz
```

## Database Restore

```bash
# From SQL file
mysql -h host -u user -p database_name < backup.sql

# From compressed file
gunzip < backup.sql.gz | mysql -h host -u user -p database_name
```

## Object Storage Backup

### Filesystem Store

```bash
# Sync to backup location
rsync -av /data/datajoint-store/ /backup/datajoint-store/

# With compression
tar -czvf store-backup.tar.gz /data/datajoint-store/
```

### S3/MinIO Store

```bash
# Using AWS CLI
aws s3 sync s3://source-bucket s3://backup-bucket

# Using MinIO client
mc mirror source/bucket backup/bucket
```

## Backup Script Example

```bash
#!/bin/bash
# backup-datajoint.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups/datajoint

# Backup database
mysqldump -h $DJ_HOST -u $DJ_USER -p$DJ_PASS \
    --databases my_schema \
    | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup object storage
rsync -av /data/store/ $BACKUP_DIR/store_$DATE/

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -mtime +7 -delete

echo "Backup completed: $DATE"
```

## Point-in-Time Recovery

### Enable Binary Logging

In MySQL configuration:

```ini
[mysqld]
log-bin = mysql-bin
binlog-format = ROW
expire_logs_days = 7
```

### Restore to Point in Time

```bash
# Restore base backup
mysql -h host -u user -p < backup.sql

# Apply binary logs up to specific time
mysqlbinlog --stop-datetime="2024-01-15 14:30:00" \
    mysql-bin.000001 mysql-bin.000002 \
    | mysql -h host -u user -p
```

## Schema-Level Export

Export schema structure without data:

```bash
# Structure only
mysqldump -h host -u user -p --no-data database_name > schema.sql
```

## Table-Level Backup

Backup specific tables:

```bash
mysqldump -h host -u user -p database_name table1 table2 > tables.sql
```

## DataJoint-Specific Considerations

### Foreign Key Order

When restoring, tables must be created in dependency order. mysqldump handles this automatically, but manual restoration may require:

```bash
# Disable FK checks during restore
mysql -h host -u user -p -e "SET FOREIGN_KEY_CHECKS=0; SOURCE backup.sql; SET FOREIGN_KEY_CHECKS=1;"
```

### Jobs Tables

Jobs tables (`~~table_name`) are recreated automatically. You can exclude them:

```bash
# Exclude jobs tables from backup
mysqldump -h host -u user -p database_name \
    --ignore-table=database_name.~~table1 \
    --ignore-table=database_name.~~table2 \
    > backup.sql
```

### Blob Data

Blobs stored internally (in database) are included in mysqldump. External objects need separate backup.

## Verification

### Verify Database Backup

```bash
# Check backup file
gunzip -c backup.sql.gz | head -100

# Restore to test database
mysql -h host -u user -p test_restore < backup.sql
```

### Verify Object Storage

```python
import datajoint as dj

# Check external objects are accessible
for key in MyTable.fetch('KEY'):
    try:
        (MyTable & key).fetch1('blob_column')
    except Exception as e:
        print(f"Missing: {key} - {e}")
```

## Disaster Recovery Plan

1. **Regular backups**: Daily database, continuous object sync
2. **Offsite copies**: Replicate to different location/cloud
3. **Test restores**: Monthly restore verification
4. **Document procedures**: Written runbooks for recovery
5. **Monitor backups**: Alert on backup failures

## See Also

- [Configure Object Storage](configure-storage.md) — Storage setup
- [Manage Large Data](manage-large-data.md) — Object storage patterns
