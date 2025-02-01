FROM ubuntu:20.04
#VOLUME ["/input", "/output"]
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
#ENV HTTPS_PROXY=http://172.20.0.252:3128
#ENV HTTP_PROXY=http://172.20.0.252:3128
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y git cmake build-essential wget

#RUN git config --global http.proxy http://172.20.0.252:3128
#RUN git config --global https.proxy http://172.20.0.252:3128

RUN apt-get update && apt-get install -y \
libtiff-dev libgeotiff-dev libgdal-dev \
libboost-system-dev libboost-thread-dev libboost-filesystem-dev libboost-program-options-dev libboost-regex-dev \
libboost-iostreams-dev libtbb-dev parallel

WORKDIR /opt

# install LAStools
RUN git clone https://github.com/m-schuetz/LAStools.git && cd LAStools/LASzip && mkdir build && cd build && \
cmake -DCMAKE_BUILD_TYPE=Release .. && make && make install && ldconfig

# install PotreeConverter
RUN git clone -b develop https://github.com/potree/PotreeConverter.git && cd PotreeConverter && mkdir build && cd build && \
cmake -DCMAKE_BUILD_TYPE=Release -DLASZIP_INCLUDE_DIRS=/opt/LAStools/LASzip/dll/ -DLASZIP_LIBRARY=/usr/local/lib/liblaszip.so .. && \
make && cp -r /opt/PotreeConverter/resources /opt/PotreeConverter/build/resources

RUN apt-get install -y python3 python3-pip 
#RUN apt-get install -y binutils libproj-dev gdal-bin libgdal-dev

#RUN pip install django

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# Install miniconda
ENV CONDA_DIR=/opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda

# Put conda in path so we can use conda activate
ENV PATH=$CONDA_DIR/bin:$PATH
RUN conda config --add channels conda-forge
RUN conda config --set channel_priority flexible
RUN conda update -n base --all
RUN conda install -n base mamba

#RUN conda config --remove-key channels
#RUN conda config --set solver classic

RUN mamba install python==3.10
RUN mamba install proj 
RUN mamba install proj-data
RUN mamba install gdal
RUN mamba install pdal
RUN mamba install django
RUN mamba install affine
RUN mamba install ezdxf==1.2.0
RUN mamba install django-cors-headers
ENV PROJ_LIB=/opt/conda/share/proj

WORKDIR /app

#RUN /opt/conda/bin/python manage.py collectstatic

EXPOSE 8008
