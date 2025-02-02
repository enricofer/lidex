# Modeled from: https://vuejs.org/v2/cookbook/dockerize-vuejs-app.htm

# build stage
FROM node:lts-alpine 
# as build-stage

# ENV HTTPS_PROXY=http://172.20.0.252:3128
# ENV HTTP_PROXY=http://172.20.0.252:3128
# ENV NODE_ENV=development


RUN apk update
RUN apk add --no-cache git
RUN rm -rf /var/cache/apk/*

RUN git clone -b master --single-branch https://github.com/wegue-oss/wegue.git /app
#COPY ./wegue_common /app

WORKDIR /app

RUN npm install
RUN npm install html2canvas
RUN npm install jspdf
RUN npm install ol-ext
RUN npm install proj4
RUN npm install jsonp
RUN npm install eslint -g -D
RUN eslint --init

#COPY . .
#RUN npm run init:app
EXPOSE 8081
CMD ["npm", "run", "serve"] 

# docker build -t lidex:latest ./wegue_custom_app