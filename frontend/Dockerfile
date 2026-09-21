# CT Sale — frontend (SSR)
#
# Statik build yetarli emas: sahifa serverda render qilinishi kerak
# (crawler to'liq HTML ko'rishi uchun), shuning uchun yakuniy
# obrazda Node jarayoni qoladi.

FROM node:20-alpine AS builder

WORKDIR /app

# Bog'liqliklar alohida qatlamda — kod o'zgarganda qayta o'rnatilmasin
COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build


FROM node:20-alpine

ENV NODE_ENV=production

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --omit=dev && npm cache clean --force

COPY --from=builder /app/dist ./dist
COPY server.js ./

# Root'dan ishlamaslik (node obrazida `node` foydalanuvchisi bor)
USER node

EXPOSE 5173

CMD ["node", "server.js"]
