FROM nginx:latest
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# ENV HTTPS_PROXY=http://172.20.0.252:3128
# ENV HTTP_PROXY=http://172.20.0.252:3128

RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt update && apt-get -y install tzdata wget

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]