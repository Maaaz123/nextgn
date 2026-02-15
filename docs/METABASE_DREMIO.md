# Metabase → Dremio Connection

## Settings

| Field | Value |
|-------|-------|
| **Display name** | Any name (e.g. `Dremio`) |
| **Host** | `dremio` |
| **Port** | `31010` |
| **Username** | Your Dremio admin email (e.g. `m.majid@nextgn.io`) |
| **Password** | Your Dremio password |

Metabase and Dremio run in Docker on the same network. Use host **`dremio`** (service name), not `localhost`. Port **31010** is Dremio's JDBC port (9047 is the web UI).

## Prerequisites

1. **Dremio first-time setup** – Visit http://localhost:9047 and complete the wizard (create admin account). JDBC will not accept connections until this is done.
2. **Dremio fully started** – Dremio can take 2–5 minutes to start. Wait until the web UI loads before connecting from Metabase.

## Verify connectivity

From the project root:

```bash
# From host: port 31010 exposed?
nc -zv localhost 31010

# From Metabase container: can it reach Dremio? (nc may not be in image)
docker exec data_tools_metabase sh -c "command -v nc && nc -zv dremio 31010 || echo 'Run: nc -zv localhost 31010 from host'"
```

If you see `Connection refused` or a timeout, Dremio may still be starting or the JDBC service is not ready. Wait 2–5 minutes and retry. Confirm you completed the Dremio setup at http://localhost:9047.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Check your host and port" | Use `dremio` and `31010`. Ensure Dremio container is running (`docker ps`). |
| "Connection refused" | Dremio still starting. Wait 2–5 min, or check `docker logs data_tools_dremio` for errors. |
| Auth failure | Ensure you completed Dremio's first-run setup and use the exact email/password you created. |
| Malformed URL | Host must be `dremio` or `localhost` only—no `http://`, no trailing slash. |
