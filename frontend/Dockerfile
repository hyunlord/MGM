FROM node:18-alpine
WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile
COPY public/ ./public
COPY src/ ./src
RUN yarn build
CMD ["npx", "serve", "-s", "build", "-l", "3000"]