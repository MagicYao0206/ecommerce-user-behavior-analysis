# 电商用户行为分析系统 📊

基于Python+MySQL+Streamlit构建的电商用户行为分析平台，集成数据清洗、漏斗转化、时段分析、RFM用户分群及AI智能洞察，支持可视化看板与PDF报告导出，助力电商运营决策。

## 项目简介

本项目针对电商平台用户行为数据（浏览、收藏、加购、购买），提供全流程数据分析解决方案：
- 数据层：支持百万级用户行为数据清洗与MySQL存储
- 分析层：覆盖转化漏斗、时段分布、RFM用户分群核心分析场景
- 可视化层：交互式Streamlit看板+多类型图表（漏斗图、饼图、折线图）
- 智能层：集成Llama大模型生成结构化运营建议
- 输出层：支持中文PDF分析报告导出

## 核心功能

### 1. 数据清洗与存储
- 处理原始用户行为数据（时间戳转换、异常值过滤、无效数据剔除）
- 分块导入MySQL，生成`user_behavior`（原始行为数据）和`user_summary`（用户汇总数据）双表
- 支持100万行数据高效处理，避免内存溢出

### 2. 多维数据分析
| 分析模块       | 核心功能                                                                 |
|----------------|--------------------------------------------------------------------------|
| 转化漏斗分析   | 计算浏览→收藏→加购→购买全链路转化率，定位核心流失环节                     |
| 时段行为分析   | 识别24小时内用户浏览/购买高峰时段，提供精准运营时间建议                 |
| RFM用户分群    | 基于最近购买时间、购买频次、消费金额（简化版）将用户分为5类，精准用户运营 |
| AI智能洞察     | 调用Llama模型生成数据驱动的运营建议，包含转化优化、时段运营等维度       |

### 3. 可视化与报告
- 交互式Streamlit看板，支持日期筛选与实时数据刷新
- 多类型图表展示（漏斗图、饼图、折线图、柱状图）
- 中文PDF报告导出，包含核心指标、分析结论与运营建议

## 技术栈

| 类别       | 核心技术                                                                 |
|------------|--------------------------------------------------------------------------|
| 数据处理   | Python 3.8+、Pandas、NumPy                                              |
| 数据库     | MySQL 8.0、SQLAlchemy、PyMySQL                                           |
| 可视化     | Streamlit、Plotly、Matplotlib                                            |
| 智能分析   | Llama-cpp-python（纯CPU运行）                                            |
| 报告导出   | ReportLab（支持中文PDF生成）                                             |

## 环境配置

### 1. 依赖安装
```bash
# 克隆仓库后，安装依赖
pip install -r requirements.txt
```

### 2. MySQL配置
1. 本地安装MySQL 8.0，创建数据库`ecommerce_analysis`
2. 修改所有`.py`文件中`MYSQL_CONFIG`配置：
   ```python
   MYSQL_CONFIG = {
       "user": "你的MySQL用户名",
       "password": "你的MySQL密码",
       "host": "localhost",
       "port": 3306,
       "database": "ecommerce_analysis"
   }
   ```

### 3. 数据准备
1. 在项目根目录创建`data`文件夹，放入用户行为数据`user_behavior.csv`
2. 数据格式要求（无表头）：`user_id,item_id,category_id,behavior_type,timestamp`
3. 示例数据：`10001,20001,30001,pv,1511548800`

### 4. Llama模型配置（可选）
1. 在项目根目录创建`models`文件夹，放入Llama模型文件（如`llama-2-7b-chat.Q4_K_M.gguf`）
2. 模型下载地址：[Llama-2 7B Chat](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF)
3. 启动看板后，在侧边栏填写模型路径

## 快速启动

### 步骤1：数据清洗与导入MySQL
```bash
python data_cleaning.py
```
- 输出清洗后数据行数、行为类型分布
- 自动创建并导入`user_behavior`和`user_summary`表

### 步骤2：运行分析脚本（可选）
```bash
# 漏斗分析（生成HTML漏斗图）
python funnel_analysis.py

# 时段分析（生成小时维度行为分布图）
python hourly_analysis.py

# RFM分析（生成用户分群饼图）
python rfm_analysis.py
```

### 步骤3：启动交互式看板
```bash
streamlit run ecommerce_dashboard.py
```
- 浏览器自动打开看板（默认地址：http://localhost:8501）
- 支持筛选分析日期、查看多维图表、生成PDF报告

## 项目结构
```
ecommerce-user-behavior-analysis/
├── data/                  # 数据集文件夹（存放user_behavior.csv）
├── models/                # 模型文件夹（存放Llama模型文件）
├── results/               # 分析结果输出（图表、PDF报告）
├── data_cleaning.py       # 数据清洗与MySQL导入脚本
├── funnel_analysis.py     # 转化漏斗分析脚本
├── hourly_analysis.py     # 时段行为分析脚本
├── rfm_analysis.py        # RFM用户分群分析脚本
├── ecommerce_dashboard.py # Streamlit交互式看板
├── requirements.txt       # 项目依赖清单
└── README.md              # 项目说明文档
```

## 注意事项
1. 数据文件`user_behavior.csv`和Llama模型文件较大，已添加到`.gitignore`，不纳入版本控制
2. 纯CPU运行Llama模型可能较慢，建议配置8GB以上内存
3. PDF生成依赖Windows系统宋体字体（`C:\Windows\Fonts\simsun.ttc`），Linux/Mac需手动配置字体路径
4. MySQL导入时若出现权限问题，需给用户授予`CREATE TABLE`和`INSERT`权限

## 后续优化方向
- 支持多数据源导入（CSV、Excel、MongoDB）
- 增加用户复购率、品类关联分析等模块
- 优化Llama模型运行速度（支持GPU加速）
- 增加数据权限管理与多用户协作功能

<img width="1920" height="1030" alt="image" src="https://github.com/user-attachments/assets/169a9c7a-ffbc-405d-92d5-41588cd62f1b" />

