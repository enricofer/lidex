FROM ubuntu:20.04
#VOLUME ["/input", "/output"]
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HTTPS_PROXY=http://172.20.0.252:3128
ENV HTTP_PROXY=http://172.20.0.252:3128
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y git cmake build-essential wget

RUN git config --global http.proxy http://172.20.0.252:3128
RUN git config --global https.proxy http://172.20.0.252:3128

RUN apt-get update && apt-get install -y \
libtiff-dev libgeotiff-dev libgdal-dev \
libboost-system-dev libboost-thread-dev libboost-filesystem-dev libboost-program-options-dev libboost-regex-dev libboost-iostreams-dev libtbb-dev

WORKDIR /opt

# install LAStools
RUN git clone https://github.com/m-schuetz/LAStools.git && cd LAStools/LASzip && mkdir build && cd build && \
cmake -DCMAKE_BUILD_TYPE=Release .. && make && make install && ldconfig

# install PotreeConverter
RUN git clone -b develop https://github.com/potree/PotreeConverter.git && cd PotreeConverter && mkdir build && cd build && \
cmake -DCMAKE_BUILD_TYPE=Release -DLASZIP_INCLUDE_DIRS=/opt/LAStools/LASzip/dll/ -DLASZIP_LIBRARY=/usr/local/lib/liblaszip.so .. && \
make && cp -r /opt/PotreeConverter/resources /opt/PotreeConverter/build/resources

RUN apt-get install -y python3 python3-pip 
RUN apt-get install -y binutils libproj-dev gdal-bin libgdal-dev

RUN pip install django

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# Install miniconda
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda

# Put conda in path so we can use conda activate
ENV PATH=$CONDA_DIR/bin:$PATH
RUN conda config --add channels conda-forge
RUN conda config --set channel_priority strict

#RUN conda install django
#ENV PROJ_LIB=/usr/share/proj
RUN conda install proj proj-data
RUN conda install gdal
RUN conda install pdal
RUN conda install python
RUN conda install django
RUN conda install affine
RUN conda install ezdxf
RUN conda install django-cors-headers
ENV PROJ_LIB=/opt/conda/share/proj

WORKDIR /app

#RUN /opt/conda/bin/python manage.py collectstatic

EXPOSE 8008
