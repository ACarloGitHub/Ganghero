#!/bin/bash
set -e
echo "Creating VSIX manually..."
# Copia tutti i file necessari
mkdir -p extension
cp -r out extension/
cp package.json extension/
cp README.md extension/ 2>/dev/null || true
# Crea lo zip
cd extension
zip -r ../ganghero-bridge-0.1.0.vsix .
cd ..
rm -rf extension
echo "Done: ganghero-bridge-0.1.0.vsix"
ls -la *.vsix
