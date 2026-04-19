import socket


def get_local_ip():
    try:
        # 创建一个UDP连接（不会真的建立连接，只是用来获取本机网卡IP）
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # 连接一个公网地址，自动获取本机对外的网卡IP
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]

        hostname = socket.gethostname()
        print("本机计算机名称：", hostname)
        print("本机局域网 IP：", local_ip)
        return hostname, local_ip
    except Exception as e:
        print("获取IP失败：", e)
        return None, None


if __name__ == "__main__":
    get_local_ip()
