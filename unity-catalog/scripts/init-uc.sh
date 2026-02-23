#!/bin/sh
set -e

UC_API="http://unity-catalog-server:8080/api/2.1/unity-catalog"
CATALOG_NAME="datalake_uc"

# Wait for Unity Catalog server to be fully ready AND its database connection to be up
echo "=== Waiting for Unity Catalog server ==="
until curl -s "$UC_API/catalogs" | grep -q '\(catalogs\|error_code\)' 2>/dev/null; do
  echo "Waiting for Unity Catalog server..."
  sleep 5
done

# Extra wait for the DB connection inside UC to stabilise
echo "Unity Catalog HTTP is up. Waiting for internal DB connection..."
sleep 5

echo "=== Unity Catalog Initialization ==="

# Create the single Datalake catalog with retry until it succeeds
echo "Creating catalog: $CATALOG_NAME"
RETRIES=10
i=0
while [ $i -lt $RETRIES ]; do
  RESPONSE=$(curl -s -X POST "$UC_API/catalogs" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$CATALOG_NAME\", \"comment\": \"Main datalake catalog. Schemas are created per-project by the data framework.\"}")
  echo "$RESPONSE"
  # Success if response contains the catalog name, or if catalog already exists (ALREADY_EXISTS)
  if echo "$RESPONSE" | grep -q '"name"'; then
    echo "Catalog $CATALOG_NAME created successfully."
    break
  elif echo "$RESPONSE" | grep -q 'ALREADY_EXISTS'; then
    echo "Catalog $CATALOG_NAME already exists. Skipping."
    break
  else
    echo "Catalog creation failed (attempt $((i+1))/$RETRIES). Retrying in 5s..."
    sleep 5
    i=$((i+1))
  fi
done

if [ $i -eq $RETRIES ]; then
  echo "ERROR: Failed to create catalog $CATALOG_NAME after $RETRIES attempts."
  exit 1
fi

echo ""
echo "=== Unity Catalog Initialization Complete ==="
echo ""
echo "Catalog created: $CATALOG_NAME"
echo ""
echo "Project schemas will be created dynamically by the data framework:"
echo "  $CATALOG_NAME.{project}_bronze"
echo "  $CATALOG_NAME.{project}_silver"
echo "  $CATALOG_NAME.{project}_gold"
echo ""
echo "Example tables:"
echo "  $CATALOG_NAME.games_analytics_bronze.age_rating_categories"
echo "  $CATALOG_NAME.games_analytics_silver.age_rating_categories"
echo "  $CATALOG_NAME.games_analytics_gold.age_rating_categories"
