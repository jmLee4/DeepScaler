
# 临时调整同时打开文件的数量上限，否则Locust日志中会有告警
ulimit -n 63356

echo "开始发送流量"
nohup locust -f ./sendFlow/load_generator.py --headless > ./sendFlow/sendFlow.log 2>&1 &
wait
echo "结束流量"

# while true
# do
#     echo "开始发送流量"
#     nohup locust -f ./sendFlow/load_generator.py --headless > ./sendFlow/sendFlow.log 2>&1 &
#     wait
#     echo "结束流量"
# done
