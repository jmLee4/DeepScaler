
# 临时调整同时打开文件的数量上限，否则Locust日志中会有告警
ulimit -n 63356

# echo "开始发送流量"
# nohup locust -f ./sendFlow/load_generator.py --headless > ./sendFlow/sendFlow.log 2>&1 &
# wait
# echo "结束流量"

count=1

while true
do
    echo "开始发送流量"
    formatted_count=$(printf "%02d" $count)
    nohup locust -f ./sendFlow/load_generator.py --headless > ./sendFlow/locust_log/sendFlow_${formatted_count}.log 2>&1 &
    wait
    echo "结束流量"
    count=$((count + 1))
done

# 运行过程中通过Ctrl+C强行结束脚本，还需要通过 ps -ef | grep locust 并 kill -9 的方式结束后台进程，否则流量仍处于发送状态
