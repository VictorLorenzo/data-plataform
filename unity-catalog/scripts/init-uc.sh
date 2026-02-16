#!/bin/sh
set -e

UC_API="http://unity-catalog-server:8080/api/2.1/unity-catalog"

# Wait for Unity Catalog server to be fully ready
echo "=== Waiting for Unity Catalog server ==="
until curl -s "$UC_API/catalogs" > /dev/null 2>&1; do
  echo "Waiting for Unity Catalog server..."
  sleep 5
done

echo "=== Unity Catalog Initialization ==="

# Create catalogs for each medallion zone
for catalog in landing bronze silver gold; do
  echo "Creating catalog: $catalog"
  curl -s -X POST "$UC_API/catalogs" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$catalog\", \"comment\": \"Medallion $catalog zone\"}" || true
  echo ""
done

# Create default schema in each catalog
for catalog in landing bronze silver gold; do
  echo "Creating schema: $catalog.default"
  curl -s -X POST "$UC_API/schemas" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"default\", \"catalog_name\": \"$catalog\", \"comment\": \"Default schema\"}" || true
  echo ""
done

echo "=== Unity Catalog Initialization Complete ==="
echo ""
echo "Catalogs and schemas created:"
echo "  landing.default"
echo "  bronze.default"
echo "  silver.default"
echo "  gold.default"
echo ""
echo "Register tables via Spark SQL:"
echo "  CREATE TABLE gold.default.my_table"
echo "    USING delta"
echo "    LOCATION 's3a://datalake-gold/path/to/table';"
