# Imagen del frontend Next.js en modo desarrollo.
FROM node:20-slim

WORKDIR /app

# Instala dependencias primero (cache de capas).
COPY package.json package-lock.json* ./
RUN npm install

# Copia el resto del codigo.
COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
