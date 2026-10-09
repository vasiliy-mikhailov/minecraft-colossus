# Headless Minecraft dev-client box: Java 21 + Xvfb + Mesa llvmpipe (software GL) + ImageMagick + xdotool
FROM eclipse-temurin:21-jdk
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      xvfb xauth x11-utils mesa-utils libgl1 libgl1-mesa-dri libglx-mesa0 libegl1 \
      libx11-6 libxext6 libxrandr2 libxinerama1 libxcursor1 libxi6 libxxf86vm1 libxtst6 \
      libasound2t64 imagemagick xdotool procps \
    && rm -rf /var/lib/apt/lists/*
ENV LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe MESA_GL_VERSION_OVERRIDE=4.5 DISPLAY=:99
