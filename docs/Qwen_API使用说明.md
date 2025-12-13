# Qwen API 学习建议功能使用说明

## 功能概述

本系统集成了通义千问（Qwen）AI模型，为学生提供个性化的学习建议和职业规划指导。该功能会基于学生的专业背景、已选课程和当前行业趋势，生成详细的学习建议。

## 配置步骤

### 1. 安装依赖

首先确保已安装所需的Python包：

```bash
pip install -r requirements.txt
```

主要依赖包：
- `openai>=1.0.0` - OpenAI兼容接口（用于调用Qwen API）

### 2. 获取API密钥

1. 访问 [阿里云DashScope控制台](https://dashscope.console.aliyun.com/)
2. 注册/登录账号
3. 创建API密钥（API Key）
4. 复制API密钥

### 3. 设置环境变量

#### Windows系统

**方法一：临时设置（当前命令行窗口有效）**
```cmd
set DASH_SCOPE_API_KEY=your_api_key_here
```

**方法二：永久设置（推荐）**
1. 右键"此电脑" -> "属性" -> "高级系统设置"
2. 点击"环境变量"
3. 在"用户变量"或"系统变量"中点击"新建"
4. 变量名：`DASH_SCOPE_API_KEY`
5. 变量值：你的API密钥
6. 点击"确定"保存

**方法三：在代码中设置（不推荐，仅用于测试）**
在 `utils/qwen_client.py` 中修改：
```python
def __init__(self, api_key: Optional[str] = None, model: str = "qwen-plus"):
    key = api_key or os.getenv("DASH_SCOPE_API_KEY") or "your_api_key_here"  # 临时测试用
```

#### Linux/macOS系统

**临时设置（当前终端有效）**
```bash
export DASH_SCOPE_API_KEY=your_api_key_here
```

**永久设置**
编辑 `~/.bashrc` 或 `~/.zshrc` 文件，添加：
```bash
export DASH_SCOPE_API_KEY=your_api_key_here
```

然后执行：
```bash
source ~/.bashrc  # 或 source ~/.zshrc
```

### 4. 验证配置

运行以下Python代码验证配置是否正确：

```python
import os
from utils.qwen_client import QwenAdvisor

# 检查环境变量
api_key = os.getenv("DASH_SCOPE_API_KEY")
if api_key:
    print(f"✓ API密钥已设置（长度：{len(api_key)}）")
    try:
        advisor = QwenAdvisor()
        print("✓ QwenAdvisor 初始化成功")
    except Exception as e:
        print(f"✗ 初始化失败：{e}")
else:
    print("✗ 未找到 DASH_SCOPE_API_KEY 环境变量")
```

## 使用方法

### 在学生端使用

1. **登录系统**
   - 使用学生账号登录系统

2. **进入学习建议页面**
   - 在左侧菜单中点击 "🤖 学习建议"

3. **查看当前选课信息**
   - 页面会显示当前已选课程预览
   - 包括课程数量、总学分等信息

4. **生成学习建议**
   - 点击 "✨ 生成学习建议" 按钮
   - 系统会自动收集您的学生信息和已选课程
   - 调用Qwen API生成个性化建议
   - 等待几秒钟后，建议会显示在文本框中

5. **查看建议内容**
   - 建议包括：
     - **课程学习建议**：针对每门已选课程的具体建议
     - **选课结构分析**：整体选课合理性评价
     - **学习规划建议**：未来学习方向指导
     - **职业发展建议**：结合行业趋势的职业规划

6. **复制建议**
   - 点击 "📋 复制建议" 按钮可将建议复制到剪贴板
   - 方便保存或分享

7. **刷新数据**
   - 如果选课信息有更新，点击 "🔄 刷新数据" 按钮
   - 重新加载最新的选课信息

## 功能特点

### 1. 个性化建议
- 基于学生的专业、学院、年级等背景信息
- 结合已选课程的具体情况
- 考虑当前行业发展趋势

### 2. 异步处理
- API调用在后台线程执行
- 不会阻塞用户界面
- 显示加载状态提示

### 3. 错误处理
- 完善的错误提示机制
- 清晰的错误信息说明
- 日志记录便于排查问题

### 4. 用户体验
- 美观的UI界面
- 实时状态反馈
- 一键复制功能

## 注意事项

### API使用限制

1. **调用频率限制**
   - 根据您的API套餐，可能有调用频率限制
   - 建议不要频繁点击生成按钮

2. **费用说明**
   - Qwen API按调用次数或Token数计费
   - 请关注您的API使用量和费用

3. **网络要求**
   - 需要能够访问阿里云DashScope服务
   - 确保网络连接正常

### 数据隐私

- 学生信息和课程数据仅用于生成学习建议
- 数据不会存储或用于其他用途
- API调用会记录在系统日志中

### 建议质量

- AI生成的建议仅供参考
- 建议结合实际情况和导师意见
- 定期更新选课信息以获得最新建议

## 故障排查

### 问题1：提示"Qwen API key missing"

**原因**：未设置环境变量

**解决方法**：
1. 检查是否设置了 `DASH_SCOPE_API_KEY` 环境变量
2. 重启命令行/IDE窗口
3. 重新运行程序

### 问题2：API调用失败 - 连接错误（Connection error / 10061错误）

**错误信息**：
```
[WinError 10061] 由于目标计算机积极拒绝，无法连接。
Connection error.
```

**可能原因**：
- 系统配置了HTTP/HTTPS代理，但代理服务器不可用
- 网络连接问题或防火墙阻止
- API服务暂时不可用

**解决方法**：

1. **检查代理设置**（最常见原因）：
   - 代码已自动禁用代理，如果仍有问题，请检查系统代理设置
   - Windows: 设置 -> 网络和Internet -> 代理
   - 如果不需要代理，请关闭代理设置

2. **检查网络连接**：
   ```bash
   # 测试是否能访问API服务器
   ping dashscope.aliyuncs.com
   # 或在浏览器中访问
   https://dashscope.aliyuncs.com
   ```

3. **临时禁用环境变量中的代理**：
   ```cmd
   # Windows
   set HTTP_PROXY=
   set HTTPS_PROXY=
   set http_proxy=
   set https_proxy=
   ```

4. **检查防火墙**：
   - 确保防火墙允许Python程序访问网络
   - 临时关闭防火墙测试

5. **其他方法**：
   - 检查API密钥是否正确
   - 查看系统日志获取详细错误信息
   - 稍后重试（可能是服务暂时不可用）

### 问题2-1：API调用失败 - 其他错误

**可能原因**：
- API密钥无效或过期
- 网络连接问题
- API服务暂时不可用

**解决方法**：
1. 检查API密钥是否正确
2. 检查网络连接
3. 查看系统日志获取详细错误信息
4. 稍后重试

### 问题3：生成建议时间过长

**原因**：API响应较慢或网络延迟

**解决方法**：
1. 检查网络连接
2. 等待一段时间（通常30秒内）
3. 如果超时，会显示错误信息，可重试

### 问题4：建议内容不理想

**原因**：AI模型生成的内容可能不够准确

**解决方法**：
1. 确保学生信息和选课信息完整
2. 多次生成可能得到不同建议
3. 结合实际情况和导师意见

## 技术细节

### API调用流程

1. 收集学生信息（姓名、学号、专业、学院、年级等）
2. 获取已选课程列表（课程名、代码、学分、教师、类型等）
3. 格式化数据并构建提示词
4. 调用Qwen API（使用OpenAI兼容接口）
5. 解析返回结果并显示在UI中

### 代码结构

- `utils/qwen_client.py` - Qwen API客户端封装
- `gui/student_window.py` - 学生端UI界面（包含学习建议页面）

### 模型配置

默认使用 `qwen-plus` 模型，可在 `QwenAdvisor` 初始化时修改：

```python
advisor = QwenAdvisor(model="qwen-max")  # 使用更强大的模型
```

## 更新日志

### v1.0.0 (2025-01-XX)
- ✅ 初始版本发布
- ✅ 集成Qwen API
- ✅ 实现学习建议生成功能
- ✅ 添加UI界面和交互功能

## 联系方式

如有问题或建议，请联系项目维护者。

---

**祝使用愉快！** 🎓

