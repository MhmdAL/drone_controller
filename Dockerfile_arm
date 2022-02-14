# FROM dpulpeiro/parrot-olympe:1.8.0-python3.7-slim-buster
FROM arm32v7/ubuntu:20.04 as builder

RUN printf hello

RUN apt-get update \
    && apt-get upgrade -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y libgl1 curl sudo tzdata \
    && printf "password1234\npassword1234\n" | adduser builduser \
    && usermod -aG sudo builduser

USER builduser 

RUN mkdir -p ~/code/parrot-olympe \
    && curl -L https://github.com/Parrot-Developers/olympe/releases/download/v7.0.3/parrot-olympe-src-7.0.3.tar.gz | tar zxf - -C ~/code/parrot-olympe --strip-components=1 \
    && cd ~/code/parrot-olympe \
    && printf "password1234\n" | sudo -S ~/code/parrot-olympe/products/olympe/linux/env/postinst
    
RUN printf '\nifeq ("$(TARGET_CPU)",“pi3”)\nTARGET_GLOBAL_CFLAGS += -march=armv7-a\nTARGET_FLOAT_ABI ?= hard\nendif' >> ~/code/parrot-olympe/build/alchemy/toolchains/cpu.mk \
    && printf '\nTARGET_DEFAULT_ARM_MODE := arm\nTARGET_GLOBAL_CFLAGS_arm := -mfloat-abi=hard\nTARGET_CPU = pi3' >> ~/code/parrot-olympe/products/olympe/linux/config/product.mk \
    && mv ~/code/parrot-olympe/packages/clang/libclang/armv7a-linux-gnuabihf.tar.gz ~/code/parrot-olympe/packages/clang/libclang/armv7a-linux-gnuabihf \
    && ~/code/parrot-olympe/build.sh -p olympe-linux -t images -j

FROM --platform=linux/arm/v7 python:3.9.9-slim-bullseye

COPY --from=builder /home/builduser/code/parrot-olympe/out/olympe-linux/images /tmp/wheels

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y build-essential libgl1 \
    && cd /tmp/wheels \
    && pip install $(ls) \
    && pip install protobuf haversine \
    && adduser olympe 

USER olympe

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./dc_setup.sh ~/dc_setup.sh
COPY app/ /app/

USER root
RUN chown olympe /app
USER olympe

ENTRYPOINT ["sh", "~/dc_setup.sh"]
