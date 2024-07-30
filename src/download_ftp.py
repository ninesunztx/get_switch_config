import paramiko
import os
from datetime import datetime
import time
import logging

hostname = '169.254.1.1'
username = 'yourname' #交换机用户
password = 'yourpwd'  #交换机密码
port = 22
flag = 1
cnt = 0

# 创建日志记录器
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 创建日志格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 创建文件处理器
log_filename = os.path.join(os.getcwd(), f"log\log_{time.strftime('%Y%m%d%H%M%S', time.localtime())}.log")
file_handler = logging.FileHandler(log_filename)
file_handler.setFormatter(formatter)
# 创建终端处理器
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
# 将处理器添加到日志记录器
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


class download_config:
    def __init__(self, server, username, password, port):
        self.server = server
        self.username = username
        self.password = password
        self.port = port
        self.client = self.create_ssh_client()

    def create_ssh_client(self):
        retries = 3
        for i in range(retries):
            logging.info(f"尝试连接到 {self.server} (尝试 {i+1}/{retries})")
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(
                    self.server, 
                    port=self.port, 
                    username=self.username, 
                    password=self.password, 
                    look_for_keys=False, 
                    timeout=10
                )
                logging.info(f"成功连接到 {self.server}")
                return client
            except paramiko.AuthenticationException:
                logging.error("认证失败，检查用户名或密码")
            except paramiko.SSHException as sshException:
                logging.error(f"无法建立SSH连接: {sshException}")
            except Exception as e:
                logging.error(f"连接到 {self.server} 时出错: {e}")
                time.sleep(5)  # 等待5秒后重试
        logging.error(f"无法连接到 {self.server}，已尝试 {retries} 次")
        global flag
        flag = 0
        return None
    
    def put_switch_configuration(self):
        if not self.client:
            logging.error("SSH客户端未连接")
            return "Error: SSH client not connected"
        try:
            logging.info("正在备份交换机配置")
            channel = self.client.invoke_shell()
            time.sleep(3)
            
            directory = str(datetime.now().strftime("%Y_%m_%d"))
            commands_1 = [
            "ftp xxx.xxx.xxx.xxx\n", #ftp服务端IP
            "xxx\n", #ftp服务端用户
            "xxx\n", #ftp服务端密码
            f"mkdir {directory}\n",
            f"put startup.cfg {directory}/{hostname}_startup.cfg\n",
            "quit\n",
            ]
            
            commands_2 = [
            "ftp xxx.xxx.xxx\n",
            "xxx\n",
            "xxx\n",
            f"put startup.cfg {directory}/{hostname}_startup.cfg\n",
            "quit\n",
            ]
            
            global cnt
            if cnt == 0:
                commands = commands_1
            else:
                commands = commands_2
                
            for command in commands:
                channel.send(command)
                time.sleep(3)
                output = channel.recv(65535).decode()
                logging.info(output)  # Log the output of each command
            logging.info("交换机配置备份成功")
            cnt = cnt + 1
        except Exception as e:
            logging.error(f"备份配置时出错: {e}")
            return f"Error retrieving configuration: {e}"
        finally:
            self.client.close()
            
    def save_switch_config(self):
        if not self.client:
            logging.error("SSH客户端未连接")
            return "Error: SSH client not connected"
        try:
            logging.info("正在保存交换机配置")
            channel = self.client.invoke_shell()
            time.sleep(3)
            command = "save force\n"
            channel.send(command)
            time.sleep(3)
            output = channel.recv(65535).decode()
            logging.info(output)
            logging.info("交换机配置保存完成")
        except Exception as e:
            logging.error(f"保存配置时出错：{e}")
            return f"Error retrieving configuration: {e}"
        finally:
            self.client.close()
            


def Get_config(hostname, username, password, port):
    down = download_config(hostname, username, password, port)
    try:
        down.put_switch_configuration()
        if flag == 0:
            return
    except Exception as e:
        logging.error(f'An error occurred: {e}')
        
def Save_config(hostname, username, password, port):
    down = download_config(hostname, username, password, port)
    try:
        down.save_switch_config()
        if(flag == 0):
            return
    except Exception as e:
        logging.error(f'An error occurred: {e}')


if __name__ == "__main__":
    choice = int(input("请选择操作"))
    print("1.备份交换机配置")
    print("2.保存交换机配置")
    with open("index.txt", "r") as fileHandler:
        hostname = fileHandler.readline().strip()
        while hostname:
            if choice == 1:
                Get_config(hostname, username, password, port)
            elif choice == 2:
                Save_config(hostname, username, password, port)
            else:
                print("没有此选项")
                break
            hostname = fileHandler.readline().strip()
            
    logging.info("所有操作均已处理完毕")
    os.system("pause")
