#!/bin/bash

# 长时间运行任务测试脚本
# 演示如何使用任务 ID 哈希路由和 Redis 持久化

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "长时间运行任务测试脚本"
echo "=========================================="
echo ""

# 1. 列出可用的图
echo "1. 列出可用的图..."
curl -s $BASE_URL/api/graphs | jq '.'
echo ""

# 2. 创建任务
echo "2. 创建任务..."
echo "   Graph: data_pipeline"
echo "   Initial State: {\"input\": \"test_data\"}"

TASK_RESPONSE=$(curl -s -X POST $BASE_URL/api/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "graph_name": "data_pipeline",
    "initial_state": {"input": "test_data"}
  }')

TASK_ID=$(echo $TASK_RESPONSE | jq -r '.task_id')

echo "   Response:"
echo "$TASK_RESPONSE" | jq '.'
echo ""
echo "   Task ID: $TASK_ID"
echo ""

# 3. 等待几秒，然后查询任务状态
echo "3. 等待 3 秒，查询任务状态..."
sleep 3
curl -s $BASE_URL/api/tasks/$TASK_ID | jq '.'
echo ""

# 4. 再次等待，查询任务状态
echo "4. 再等待 5 秒，查询任务状态..."
sleep 5
curl -s $BASE_URL/api/tasks/$TASK_ID | jq '.'
echo ""

# 5. 暂停任务
echo "5. 暂停任务..."
curl -s -X POST $BASE_URL/api/tasks/$TASK_ID/pause | jq '.'
echo ""

# 6. 查询任务状态
echo "6. 查询任务状态（应该显示 paused）..."
curl -s $BASE_URL/api/tasks/$TASK_ID | jq '.'
echo ""

# 7. 恢复任务
echo "7. 恢复任务（从检查点继续）..."
curl -s -X POST $BASE_URL/api/tasks/$TASK_ID/resume | jq '.'
echo ""

# 8. 等待任务完成
echo "8. 等待 15 秒，任务应该完成..."
sleep 15
curl -s $BASE_URL/api/tasks/$TASK_ID | jq '.'
echo ""

# 9. 列出所有任务
echo "9. 列出所有任务..."
curl -s $BASE_URL/api/tasks | jq '.tasks'
echo ""

# 10. 测试任务 ID 哈希路由
echo "10. 测试任务 ID 哈希路由..."
echo "    多次查询同一个任务，应该路由到同一节点..."

for i in {1..5}; do
    echo "    查询 $i:"
    NODE=$(curl -s $BASE_URL/api/tasks/$TASK_ID | jq -r '.node')
    echo "    路由到: $NODE"
    sleep 1
done

echo ""
echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "注意事项："
echo "1. 所有关于 task_abc123 的请求都路由到同一节点"
echo "2. 任务状态持久化到 Redis"
echo "3. 支持暂停、恢复、取消"
echo "4. 支持断点恢复"
echo ""
