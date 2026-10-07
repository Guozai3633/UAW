# 开发数据的维护与恢复

范围：本轮创建的uaw-development PostgreSQL实例。以下操作说明不表示已完成生产恢复演练。

## 迁移与版本

```powershell
./ops/start-dev-db.ps1
./.venv/Scripts/python.exe -m alembic upgrade head
```

当前head为0002_immutable_versions。应用检查该版本，不自动建表或降级；数据库版本不匹配就拒绝就绪。后续变更追加迁移，不修改已经执行过的迁移。

## 备份

```powershell
New-Item -ItemType Directory -Path .data/backups -Force | Out-Null
docker exec uaw-development-postgres-1 pg_dump -U uaw_dev -d uaw_dev -Fc -f /tmp/uaw-backup.dump
docker cp uaw-development-postgres-1:/tmp/uaw-backup.dump .data/backups/uaw-backup.dump
```

备份包含输入和运行资料，按私有数据管理。复制blob目录及对应SQL引用时，先停止写入或记录一致的备份边界；仅复制数据库不代表所有大内容已经备份。

## 恢复

恢复到新数据库/私有blob目录，检查迁移版本、主体归属、引用和Hash后才切换应用配置。不能在正在运行的权威库中直接覆盖状态，也不能仅从旧快照恢复已被撤销的权限。

具体全量恢复脚本与故障演练属于后续交付；本轮真实验证的是独立进程可读取已提交原文、冲突回滚、重复请求/消费者去重和版本删除约束。

