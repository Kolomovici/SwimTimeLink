# check_mqtt_status.py
"""
检查ESP.py运行时MQTT的状态
"""

import socket
import subprocess
import sys
import time

print("=== 检查MQTT状态 ===")

def check_port(host='localhost', port=1883):
    """检查MQTT端口是否开放"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ 端口 {port} 已开放 (MQTT Broker可能正在运行)")
            return True
        else:
            print(f"❌ 端口 {port} 未开放 (MQTT Broker可能未运行)")
            return False
    except Exception as e:
        print(f"❌ 检查端口时出错: {e}")
        return False

def check_mqtt_service():
    """检查MQTT服务状态"""
    print("\n=== 检查MQTT服务 ===")
    
    # Windows服务检查
    try:
        result = subprocess.run(
            ['sc', 'query', 'mosquitto'], 
            capture_output=True, 
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if 'RUNNING' in result.stdout:
            print("✅ Mosquitto服务正在运行")
            return True
        else:
            print("❌ Mosquitto服务未运行")
            return False
            
    except FileNotFoundError:
        print("ℹ️ 未找到Mosquitto服务，尝试其他检查方法")
        return check_port()

def test_mqtt_connection():
    """测试MQTT连接"""
    print("\n=== 测试MQTT连接 ===")
    
    try:
        import paho.mqtt.client as mqtt
        
        connected = False
        error_message = ""
        
        def on_connect(client, userdata, flags, rc):
            nonlocal connected, error_message
            if rc == 0:
                connected = True
            else:
                error_message = f"连接返回码: {rc}"
        
        # 创建测试客户端
        client = mqtt.Client(client_id="test_client_check")
        client.on_connect = on_connect
        client.connect_timeout = 3
        
        try:
            client.connect("localhost", 1883, 60)
            client.loop_start()
            time.sleep(2)  # 等待连接
            client.loop_stop()
            client.disconnect()
            
            if connected:
                print("✅ MQTT连接测试成功")
                return True
            else:
                print(f"❌ MQTT连接失败: {error_message}")
                return False
                
        except Exception as e:
            print(f"❌ MQTT连接异常: {e}")
            return False
            
    except ImportError:
        print("❌ 未安装paho-mqtt库")
        print("请运行: pip install paho-mqtt")
        return False

def check_esp_mqtt_usage():
    """检查ESP.py中MQTT的使用情况"""
    print("\n=== 检查ESP.py中的MQTT配置 ===")
    
    try:
        with open('ESP.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找MQTT相关配置
        import re
        
        # 查找broker配置
        broker_match = re.search(r'self\.broker\s*=\s*["\']([^"\']+)["\']', content)
        if broker_match:
            print(f"✅ Broker地址: {broker_match.group(1)}")
        else:
            print("❌ 未找到broker配置")
        
        # 查找端口配置
        port_match = re.search(r'self\.port\s*=\s*(\d+)', content)
        if port_match:
            print(f"✅ Broker端口: {port_match.group(1)}")
        else:
            print("❌ 未找到端口配置")
        
        # 检查MQTT导入
        if 'import paho.mqtt.client' in content or 'import mqtt' in content:
            print("✅ ESP.py导入了MQTT库")
        else:
            print("❌ ESP.py可能未导入MQTT库")
            
        # 检查add_device方法中的MQTT使用
        if 'mqtt.Client' in content:
            print("✅ ESP.py使用了mqtt.Client")
        else:
            print("❌ ESP.py中未找到mqtt.Client使用")
            
    except Exception as e:
        print(f"❌ 读取ESP.py时出错: {e}")

def check_system_ports():
    """检查系统端口使用情况"""
    print("\n=== 检查系统端口 ===")
    
    try:
        # Windows查看端口占用
        result = subprocess.run(
            ['netstat', '-ano'], 
            capture_output=True, 
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        mqtt_ports = []
        for line in result.stdout.split('\n'):
            if ':1883' in line and 'LISTENING' in line:
                mqtt_ports.append(line.strip())
        
        if mqtt_ports:
            print("✅ 发现MQTT端口监听:")
            for port_info in mqtt_ports:
                print(f"  {port_info}")
        else:
            print("❌ 未发现1883端口监听")
            
    except Exception as e:
        print(f"❌ 检查端口时出错: {e}")

def main():
    """主检查函数"""
    
    print("开始检查MQTT状态...\n")
    
    # 1. 检查端口
    port_open = check_port()
    
    # 2. 检查服务
    service_running = check_mqtt_service()
    
    # 3. 检查ESP.py配置
    check_esp_mqtt_usage()
    
    # 4. 检查系统端口
    check_system_ports()
    
    # 5. 测试连接
    if port_open:
        connection_ok = test_mqtt_connection()
    else:
        print("\n⚠️  由于端口未开放，跳过连接测试")
        connection_ok = False
    
    # 总结
    print("\n" + "="*50)
    print("检查结果总结:")
    print("="*50)
    
    if port_open and connection_ok:
        print("✅ MQTT状态正常！ESP.py可以正常添加设备")
        print("\n下一步:")
        print("1. 运行ESP.py")
        print("2. 按 'a' 或 'A' 键添加设备")
        print("3. 输入设备ID")
    elif port_open and not connection_ok:
        print("⚠️  MQTT端口开放但连接测试失败")
        print("可能原因:")
        print("  - Broker需要认证")
        print("  - 防火墙阻止")
        print("  - Broker配置问题")
    elif not port_open:
        print("❌ MQTT Broker未运行")
        print("\n解决方案:")
        print("1. 安装并启动MQTT Broker:")
        print("   - Mosquitto: https://mosquitto.org/download/")
        print("   - EMQX: https://www.emqx.io/downloads")
        print("2. 或使用Docker运行:")
        print("   docker run -d -p 1883:1883 eclipse-mosquitto")
        print("3. 启动后重新检查")
    else:
        print("❌ 未知状态")
    
    print("\n快速启动MQTT Broker:")
    print("1. 下载Mosquitto Windows版本")
    print("2. 安装后运行: net start mosquitto")
    print("3. 或命令行运行: mosquitto -v")

if __name__ == "__main__":
    main()