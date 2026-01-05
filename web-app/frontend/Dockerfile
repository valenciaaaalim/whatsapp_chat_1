FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY public ./public
COPY src ./src

EXPOSE 3000

ENV HOST=0.0.0.0

CMD ["npm", "start"]
