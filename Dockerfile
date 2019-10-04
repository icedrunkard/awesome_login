# build awesome_login image
FROM icedrunkard/python36:latest
# icedrunkard/python36:latest 镜像中的workdir 是/data，
# 把当前文件夹内所有文件和文件夹复制到/data文件夹下
ADD . /data
# It's a good idea to use dumb-init to help prevent zombie processes.
RUN wget -O /usr/local/bin/dumb-init https://github.com/Yelp/dumb-init/releases/download/v1.2.2/dumb-init_1.2.2_amd64
RUN chmod +x /usr/local/bin/dumb-init
RUN pip install pillow aiohttp -i https://pypi.tuna.tsinghua.edu.cn/simple
EXPOSE 4002

ENTRYPOINT ["dumb-init", "--"]
CMD ["python", "/data/server.py"]