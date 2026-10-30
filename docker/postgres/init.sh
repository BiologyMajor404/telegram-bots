#!/bin/sh
# Runs once, when an empty Postgres volume starts for the first time. Each bot gets its own
# database and its own user that can reach only that database, so trouble in one bot can't
# touch the others' data. The passwords come from .env through docker-compose.yml.
set -e

for bot in slotbook chatguard splitmate jobradar; do
    eval "password=\${$(echo "$bot" | tr a-z A-Z)_DB_PASSWORD}"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres \
        -v bot="$bot" -v password="$password" <<'SQL'
CREATE ROLE :"bot" LOGIN PASSWORD :'password';
CREATE DATABASE :"bot" OWNER :"bot";
REVOKE ALL ON DATABASE :"bot" FROM PUBLIC;
SQL
done

# The admin's own databases aren't for the bots either
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres -v admin_db="$POSTGRES_DB" <<'SQL'
REVOKE CONNECT ON DATABASE postgres FROM PUBLIC;
REVOKE CONNECT ON DATABASE template1 FROM PUBLIC;
REVOKE CONNECT ON DATABASE :"admin_db" FROM PUBLIC;
SQL
