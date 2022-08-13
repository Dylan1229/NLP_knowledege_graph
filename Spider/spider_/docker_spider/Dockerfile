# 以py3.7作为基础镜像
FROM python:3.7

# 代码添加到spider文件夹
ADD ./spider /spider

# 设置code文件夹是工作目录
WORKDIR /spider

# 安装支持
RUN pip install -r requirements.txt

# 当启动容器时，执行sina_slaver.py程序
CMD ["python", "/spider/sina_slaver_oldnews.py"]