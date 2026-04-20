# Install required npm packages
npm install @mui/material @emotion/react @emotion/styled
npm install @mui/icons-material
npm install react-router-dom
npm install @types/react @types/react-dom @types/react-router-dom --save-dev

# Install TypeScript and related dependencies
npm install --save-dev typescript @types/node @types/react @types/react-dom

# Create tsconfig.json if it doesn't exist
if (-not (Test-Path "tsconfig.json")) {
    npx tsc --init --jsx react-jsx --esModuleInterop true --resolveJsonModule true --isolatedModules true --target es2020 --lib es2020,dom --module esnext --moduleResolution node
}

Write-Host "Setup complete. You can now run 'npm run dev' to start the development server."
