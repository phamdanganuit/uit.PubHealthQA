#!/bin/bash
# Fix Azure Students Region Policy Error

echo "🔧 Fixing Azure Region Policy Error for Azure Students..."

# Option 1: Use Azure CLI with allowed region (Recommended)
echo "Deploying to Malaysia West region..."
az webapp up --resource-group pubhealth-rg --name pubhealth-qa-app-new --runtime "PYTHON:3.11" --sku B1 --location "malaysiawwest"

# If Malaysia West fails, try these alternatives:
# az webapp up --resource-group pubhealth-rg --name pubhealth-qa-app-new --runtime "PYTHON:3.11" --sku B1 --location "japanwest"
# az webapp up --resource-group pubhealth-rg --name pubhealth-qa-app-new --runtime "PYTHON:3.11" --sku B1 --location "koreacentral"
# az webapp up --resource-group pubhealth-rg --name pubhealth-qa-app-new --runtime "PYTHON:3.11" --sku B1 --location "indonesiacentral"

echo "✅ Deployment completed! Don't forget to configure Environment Variables in Azure Portal."