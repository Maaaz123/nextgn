# Metabase plugins (Dremio driver)

The Dremio driver (`dremio.metabase-driver.jar`) is pre-installed from [metabase-dremio-driver](https://github.com/Baoqi/metabase-dremio-driver).

**To add Dremio in Metabase:**
1. Open Metabase → **Admin** → **Databases** → **Add database**
2. Choose **Dremio** from the database type list
3. Host: `dremio` (or `localhost` if not in Docker), Port: `9047`
4. Enter Dremio credentials

If Dremio does not appear, run: `docker compose up -d metabase --force-recreate`
