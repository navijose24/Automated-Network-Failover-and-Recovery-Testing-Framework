# SQLite Database Schema & Entity Relationships

The framework utilizes an embedded SQLite database (`failover_framework.db`) with Write-Ahead Logging (`PRAGMA journal_mode = WAL`) to support high-frequency concurrent telemetry writes from the packet monitor thread and dashboard reads.

---

## 1. Entity-Relationship Diagram

```
+--------------------------------------------------------+
|                      sessions                          |
+--------------------------------------------------------+
| PK  id                     INTEGER AUTOINCREMENT       |
|     session_name           TEXT                        |
|     scenario_name          TEXT                        |
|     start_time             REAL                        |
|     end_time               REAL                        |
|     status                 TEXT                        |
|     failback_enabled       INTEGER                     |
|     config_json            TEXT                        |
+--------------------------------------------------------+
       |                           |                     |
  1:N  |                      1:N  |                1:1  |
       v                           v                     v
+-----------------------+  +--------------------+  +--------------------------------+
|     probe_records     |  |   network_events   |  |        session_metrics         |
+-----------------------+  +--------------------+  +--------------------------------+
| PK  id                |  | PK  id             |  | PK  id                         |
| FK  session_id        |  | FK  session_id     |  | FK  session_id (UNIQUE)       |
|     timestamp         |  |     timestamp      |  |     failure_detection_time_ms  |
|     sequence_num      |  |     event_type     |  |     failover_recovery_time_ms  |
|     target_ip         |  |     scenario       |  |     failback_recovery_time_ms  |
|     success           |  |     affected_iface |  |     packet_loss_percent        |
|     rtt_ms            |  |     details        |  |     availability_percent       |
|     active_interface  |  +--------------------+  |     avg_latency_ms             |
|     active_path       |                          |     min_latency_ms             |
+-----------------------+                          |     max_latency_ms             |
                                                   |     total_probes               |
                                                   |     successful_probes          |
                                                   |     failed_probes              |
                                                   |     failover_success           |
                                                   +--------------------------------+
```

---

## 2. Table Specifications

### 1. `sessions` Table
Stores high-level metadata for each experiment run.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique session identifier. |
| `session_name` | TEXT | NOT NULL | User-assigned or generated test name. |
| `scenario_name` | TEXT | NOT NULL | Failure scenario evaluated in this session. |
| `start_time` | REAL | NOT NULL | Unix epoch timestamp of session initiation. |
| `end_time` | REAL | NULL | Unix epoch timestamp of session termination. |
| `status` | TEXT | NOT NULL DEFAULT 'RUNNING' | Current state: `'RUNNING'`, `'COMPLETED'`, `'FAILED'`. |
| `failback_enabled`| INTEGER | NOT NULL DEFAULT 0 | Boolean flag (0/1) for automatic failback. |
| `config_json` | TEXT | NULL | JSON dump of experiment configuration parameters. |

---

### 2. `probe_records` Table
Stores high-resolution individual ICMP ping measurements.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique measurement ID. |
| `session_id` | INTEGER | FOREIGN KEY (sessions.id) | Owning experiment session. |
| `timestamp` | REAL | NOT NULL | Unix epoch timestamp of probe transmission. |
| `sequence_num` | INTEGER | NOT NULL | Monotonically increasing ICMP sequence number. |
| `target_ip` | TEXT | NOT NULL | Destination host probed (`10.50.0.1`). |
| `success` | INTEGER | NOT NULL | 1 if ICMP echo reply received, 0 if lost/timed out. |
| `rtt_ms` | REAL | NULL | Round-trip time in milliseconds (null on loss). |
| `active_interface`| TEXT | NULL | Linux device utilized for egress (`veth_c_p` or `veth_c_b`). |
| `active_path` | TEXT | NOT NULL | Path name: `'PRIMARY'` or `'BACKUP'`. |

---

### 3. `network_events` Table
Audit trail of lifecycle transitions and failure injections.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique event identifier. |
| `session_id` | INTEGER | FOREIGN KEY (sessions.id) | Owning experiment session. |
| `timestamp` | REAL | NOT NULL | Unix epoch timestamp of event occurrence. |
| `event_type` | TEXT | NOT NULL | Lifecycle code: `'FAILURE_TRIGGERED'`, `'FAILURE_DETECTED'`, `'FAILOVER_ACTIVATED'`, `'FAILOVER_COMPLETED'`, `'PRIMARY_RESTORED'`, `'FAILBACK_COMPLETED'`. |
| `scenario` | TEXT | NULL | Associated scenario ID. |
| `affected_interface`| TEXT | NULL | Interface impacted by event. |
| `details` | TEXT | NULL | JSON encoded context and measurements. |

---

### 4. `session_metrics` Table
Aggregated quantitative resilience evaluation per session.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique metrics entry ID. |
| `session_id` | INTEGER | UNIQUE, FK (sessions.id) | One-to-one foreign key with session. |
| `failure_detection_time_ms` | REAL | NULL | Detection time: $T_{detect} - T_{failure}$ in ms. |
| `failover_recovery_time_ms` | REAL | NULL | Recovery time: $T_{restored} - T_{failure}$ in ms. |
| `failback_recovery_time_ms` | REAL | NULL | Failback duration: $T_{failback\_complete} - T_{primary\_restored}$ in ms. |
| `packet_loss_percent` | REAL | NOT NULL | Ratio of dropped packets to total transmitted ($\times 100$). |
| `availability_percent` | REAL | NOT NULL | Ratio of successful checks to total checks ($\times 100$). |
| `avg_latency_ms` | REAL | NOT NULL | Arithmetic mean round-trip latency of successful probes. |
| `min_latency_ms` | REAL | NOT NULL | Lowest round-trip latency recorded. |
| `max_latency_ms` | REAL | NOT NULL | Highest round-trip latency recorded. |
| `total_probes` | INTEGER | NOT NULL | Total count of ICMP packets dispatched. |
| `successful_probes` | INTEGER | NOT NULL | Total count of received ICMP replies. |
| `failed_probes` | INTEGER | NOT NULL | Total count of lost packets. |
| `failover_success` | INTEGER | NOT NULL | Boolean flag (0/1) indicating successful route switch. |
