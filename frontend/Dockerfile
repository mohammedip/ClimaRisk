FROM node:18-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build
# On utilise un serveur simple pour le développement ou nginx pour la prod
RUN npm install -g serve
CMD ["serve", "-s", "build", "-l", "3000"]