#!/bin/bash
# Execute all tutorial notebooks with outputs saved
# Uses PostgreSQL backend with TLS disabled to avoid SSL warnings in output

set -e

cd "$(dirname "$0")/.."

# Database connection settings for PostgreSQL
export DJ_HOST=localhost
export DJ_PORT=5432
export DJ_USER=postgres
export DJ_PASS=tutorial
export DJ_BACKEND=postgresql
export DJ_USE_TLS=false

echo "Executing tutorials with PostgreSQL backend..."
echo "  Host: $DJ_HOST:$DJ_PORT"
echo "  User: $DJ_USER"
echo "  Backend: $DJ_BACKEND"
echo "  TLS: disabled"
echo ""

# Execute all tutorial notebooks
echo "Executing basics tutorials..."
jupyter nbconvert --to notebook --execute --inplace src/tutorials/basics/*.ipynb

echo "Executing advanced tutorials..."
jupyter nbconvert --to notebook --execute --inplace src/tutorials/advanced/*.ipynb

echo "Executing domain tutorials..."
for dir in src/tutorials/domain/*/; do
    echo "  Executing $dir..."
    jupyter nbconvert --to notebook --execute --inplace "$dir"*.ipynb
done

echo "Executing how-to notebooks..."
jupyter nbconvert --to notebook --execute --inplace src/how-to/*.ipynb

echo ""
echo "All notebooks executed successfully!"
