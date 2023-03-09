FROM python:3.9-buster

ENV PATH "${PATH}:/pop-fe"

WORKDIR /pop-fe

RUN apt-get update && apt-get install -y \
  libsndfile-dev \
  python3-opencv \
  cmake && \
  rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
  requests_cache==0.9.1 \
  pycdlib==1.12.0 \
  ecdsa==0.17.0 \
  Pillow==9.0.0 \
  pycrypto==2.6.1 \
  opencv-python

RUN git clone https://github.com/NRGDEAD/Cue2cu2.git /usr/src/Cue2cu2 && \
  git clone https://github.com/putnam/binmerge.git /usr/src/binmerge && \
  git clone https://github.com/dcherednik/atracdenc.git /usr/src/atracdenc && \
  git clone -b use-python3 https://github.com/sahlberg/PSL1GHT.git /usr/src/PSL1GHT

RUN \
  cd /usr/src/PSL1GHT/tools/ps3py && \
  make && \
  cd /usr/src/atracdenc/src && \
  cmake . && \
  make

RUN \
  cp -R /usr/src/atracdenc/ . && \
  cp /usr/src/Cue2cu2/cue2cu2.py . && \
  chmod +x cue2cu2.py && \
  cp /usr/src/binmerge/binmerge . && \
  chmod +x binmerge


COPY . .

ENTRYPOINT [ "python", "./pop-fe.py" ]
